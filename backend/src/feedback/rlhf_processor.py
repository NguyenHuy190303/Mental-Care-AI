"""
RLHF (Reinforcement Learning from Human Feedback) Data Processor
Processes user feedback to improve the Mental Health Agent's responses.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from ..database import get_db_session
from ..models.database import FeedbackEntry, UserInteraction
from .feedback_collector import FeedbackType, FeedbackRating
from ..monitoring.logging_config import get_logger

logger = get_logger("feedback.rlhf")


class ResponseQuality(str, Enum):
    """Response quality categories for RLHF."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    HARMFUL = "harmful"


@dataclass
class RLHFDataPoint:
    """Single data point for RLHF training."""
    
    user_input: str
    agent_response: str
    human_feedback_score: float
    quality_category: ResponseQuality
    feedback_metadata: Dict[str, Any]
    interaction_id: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'user_input': self.user_input,
            'agent_response': self.agent_response,
            'human_feedback_score': self.human_feedback_score,
            'quality_category': self.quality_category.value,
            'feedback_metadata': self.feedback_metadata,
            'interaction_id': self.interaction_id,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class RLHFDataset:
    """Dataset for RLHF training."""
    
    data_points: List[RLHFDataPoint]
    metadata: Dict[str, Any]
    created_at: datetime
    
    def __len__(self) -> int:
        return len(self.data_points)
    
    def get_quality_distribution(self) -> Dict[str, int]:
        """Get distribution of quality categories."""
        distribution = {}
        for point in self.data_points:
            category = point.quality_category.value
            distribution[category] = distribution.get(category, 0) + 1
        return distribution
    
    def get_average_score(self) -> float:
        """Get average feedback score."""
        if not self.data_points:
            return 0.0
        return sum(point.human_feedback_score for point in self.data_points) / len(self.data_points)
    
    def filter_by_quality(self, min_quality: ResponseQuality) -> 'RLHFDataset':
        """Filter dataset by minimum quality."""
        quality_order = {
            ResponseQuality.HARMFUL: 0,
            ResponseQuality.POOR: 1,
            ResponseQuality.ACCEPTABLE: 2,
            ResponseQuality.GOOD: 3,
            ResponseQuality.EXCELLENT: 4
        }
        
        min_level = quality_order[min_quality]
        filtered_points = [
            point for point in self.data_points
            if quality_order[point.quality_category] >= min_level
        ]
        
        return RLHFDataset(
            data_points=filtered_points,
            metadata={**self.metadata, 'filtered_by': min_quality.value},
            created_at=datetime.utcnow()
        )
    
    def to_json(self) -> str:
        """Convert dataset to JSON."""
        return json.dumps({
            'data_points': [point.to_dict() for point in self.data_points],
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }, indent=2)


class RLHFProcessor:
    """Processes feedback data for RLHF training."""
    
    def __init__(self):
        """Initialize RLHF processor."""
        self.quality_thresholds = {
            ResponseQuality.EXCELLENT: 4.5,
            ResponseQuality.GOOD: 3.5,
            ResponseQuality.ACCEPTABLE: 2.5,
            ResponseQuality.POOR: 1.5,
            ResponseQuality.HARMFUL: 0.0
        }
        logger.info("RLHF processor initialized")
    
    async def process_feedback_for_rlhf(
        self,
        days: int = 30,
        min_feedback_count: int = 2,
        include_safety_feedback: bool = True
    ) -> RLHFDataset:
        """
        Process feedback data to create RLHF training dataset.
        
        Args:
            days: Number of days of data to include
            min_feedback_count: Minimum feedback count per interaction
            include_safety_feedback: Whether to include safety-related feedback
            
        Returns:
            RLHF dataset ready for training
        """
        try:
            logger.info(f"Processing feedback for RLHF (last {days} days)")
            
            # Get feedback data with interactions
            feedback_data = await self._get_feedback_with_interactions(
                days=days,
                min_feedback_count=min_feedback_count,
                include_safety_feedback=include_safety_feedback
            )
            
            # Process each interaction
            rlhf_points = []
            for interaction_data in feedback_data:
                try:
                    rlhf_point = await self._create_rlhf_datapoint(interaction_data)
                    if rlhf_point:
                        rlhf_points.append(rlhf_point)
                except Exception as e:
                    logger.warning(f"Failed to process interaction {interaction_data.get('interaction_id')}: {e}")
                    continue
            
            # Create dataset
            dataset = RLHFDataset(
                data_points=rlhf_points,
                metadata={
                    'processing_date': datetime.utcnow().isoformat(),
                    'days_included': days,
                    'min_feedback_count': min_feedback_count,
                    'include_safety_feedback': include_safety_feedback,
                    'total_interactions_processed': len(feedback_data),
                    'valid_datapoints_created': len(rlhf_points)
                },
                created_at=datetime.utcnow()
            )
            
            logger.info(
                f"RLHF dataset created with {len(rlhf_points)} data points",
                quality_distribution=dataset.get_quality_distribution(),
                average_score=dataset.get_average_score()
            )
            
            return dataset
            
        except Exception as e:
            logger.error(f"Failed to process feedback for RLHF: {e}")
            raise
    
    async def _get_feedback_with_interactions(
        self,
        days: int,
        min_feedback_count: int,
        include_safety_feedback: bool
    ) -> List[Dict[str, Any]]:
        """Get feedback data joined with interactions."""
        try:
            async with get_db_session() as session:
                # Build query to get interactions with feedback
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Get interactions that have feedback
                query = select(
                    UserInteraction.interaction_id,
                    UserInteraction.user_input,
                    UserInteraction.agent_response,
                    UserInteraction.created_at,
                    UserInteraction.metadata.label('interaction_metadata'),
                    func.count(FeedbackEntry.feedback_id).label('feedback_count'),
                    func.avg(FeedbackEntry.rating).label('avg_rating'),
                    func.array_agg(FeedbackEntry.feedback_type).label('feedback_types'),
                    func.array_agg(FeedbackEntry.rating).label('ratings'),
                    func.array_agg(FeedbackEntry.text_feedback).label('text_feedbacks'),
                    func.array_agg(FeedbackEntry.metadata).label('feedback_metadatas')
                ).select_from(
                    UserInteraction.__table__.join(
                        FeedbackEntry.__table__,
                        UserInteraction.interaction_id == FeedbackEntry.interaction_id
                    )
                ).where(
                    and_(
                        UserInteraction.created_at >= cutoff_date,
                        FeedbackEntry.created_at >= cutoff_date
                    )
                ).group_by(
                    UserInteraction.interaction_id,
                    UserInteraction.user_input,
                    UserInteraction.agent_response,
                    UserInteraction.created_at,
                    UserInteraction.metadata
                ).having(
                    func.count(FeedbackEntry.feedback_id) >= min_feedback_count
                )
                
                # Filter safety feedback if needed
                if not include_safety_feedback:
                    query = query.where(
                        FeedbackEntry.feedback_type != FeedbackType.SAFETY.value
                    )
                
                result = await session.execute(query)
                rows = result.fetchall()
                
                # Convert to list of dictionaries
                feedback_data = []
                for row in rows:
                    feedback_data.append({
                        'interaction_id': row.interaction_id,
                        'user_input': row.user_input,
                        'agent_response': row.agent_response,
                        'created_at': row.created_at,
                        'interaction_metadata': row.interaction_metadata,
                        'feedback_count': row.feedback_count,
                        'avg_rating': float(row.avg_rating) if row.avg_rating else None,
                        'feedback_types': row.feedback_types,
                        'ratings': [r for r in row.ratings if r is not None],
                        'text_feedbacks': [t for t in row.text_feedbacks if t],
                        'feedback_metadatas': row.feedback_metadatas
                    })
                
                logger.info(f"Retrieved {len(feedback_data)} interactions with feedback")
                return feedback_data
                
        except Exception as e:
            logger.error(f"Failed to get feedback with interactions: {e}")
            raise
    
    async def _create_rlhf_datapoint(self, interaction_data: Dict[str, Any]) -> Optional[RLHFDataPoint]:
        """Create RLHF data point from interaction and feedback data."""
        try:
            # Calculate composite feedback score
            feedback_score = await self._calculate_feedback_score(interaction_data)
            
            # Determine quality category
            quality_category = self._determine_quality_category(feedback_score, interaction_data)
            
            # Extract relevant metadata
            feedback_metadata = {
                'feedback_count': interaction_data['feedback_count'],
                'avg_rating': interaction_data['avg_rating'],
                'feedback_types': interaction_data['feedback_types'],
                'has_safety_concerns': FeedbackType.SAFETY.value in interaction_data['feedback_types'],
                'text_feedback_count': len(interaction_data['text_feedbacks']),
                'interaction_metadata': interaction_data.get('interaction_metadata', {})
            }
            
            # Create RLHF data point
            rlhf_point = RLHFDataPoint(
                user_input=interaction_data['user_input'],
                agent_response=interaction_data['agent_response'],
                human_feedback_score=feedback_score,
                quality_category=quality_category,
                feedback_metadata=feedback_metadata,
                interaction_id=interaction_data['interaction_id'],
                timestamp=interaction_data['created_at']
            )
            
            return rlhf_point
            
        except Exception as e:
            logger.error(f"Failed to create RLHF data point: {e}")
            return None
    
    async def _calculate_feedback_score(self, interaction_data: Dict[str, Any]) -> float:
        """Calculate composite feedback score from multiple feedback sources."""
        try:
            ratings = interaction_data['ratings']
            feedback_types = interaction_data['feedback_types']
            feedback_metadatas = interaction_data['feedback_metadatas']
            
            if not ratings:
                return 0.0
            
            # Base score from ratings
            base_score = sum(ratings) / len(ratings)
            
            # Adjust based on feedback types and metadata
            adjustments = 0.0
            
            # Safety feedback adjustment
            if FeedbackType.SAFETY.value in feedback_types:
                # Safety concerns significantly lower the score
                adjustments -= 2.0
            
            # Crisis handling feedback
            if FeedbackType.CRISIS_HANDLING.value in feedback_types:
                # Check if crisis was handled well
                for metadata in feedback_metadatas:
                    if metadata and metadata.get('crisis_handled_well') is False:
                        adjustments -= 1.5
                    elif metadata and metadata.get('crisis_handled_well') is True:
                        adjustments += 0.5
            
            # Empathy and helpfulness bonuses
            for metadata in feedback_metadatas:
                if metadata:
                    if metadata.get('response_empathetic') is True:
                        adjustments += 0.2
                    if metadata.get('response_helpful') is True:
                        adjustments += 0.2
                    if metadata.get('response_accurate') is True:
                        adjustments += 0.1
            
            # Calculate final score
            final_score = max(0.0, min(5.0, base_score + adjustments))
            
            return round(final_score, 2)
            
        except Exception as e:
            logger.error(f"Failed to calculate feedback score: {e}")
            return 0.0
    
    def _determine_quality_category(
        self,
        feedback_score: float,
        interaction_data: Dict[str, Any]
    ) -> ResponseQuality:
        """Determine quality category based on feedback score and other factors."""
        try:
            # Check for safety concerns first
            if FeedbackType.SAFETY.value in interaction_data['feedback_types']:
                return ResponseQuality.HARMFUL
            
            # Determine category based on score
            if feedback_score >= self.quality_thresholds[ResponseQuality.EXCELLENT]:
                return ResponseQuality.EXCELLENT
            elif feedback_score >= self.quality_thresholds[ResponseQuality.GOOD]:
                return ResponseQuality.GOOD
            elif feedback_score >= self.quality_thresholds[ResponseQuality.ACCEPTABLE]:
                return ResponseQuality.ACCEPTABLE
            else:
                return ResponseQuality.POOR
                
        except Exception as e:
            logger.error(f"Failed to determine quality category: {e}")
            return ResponseQuality.POOR
    
    async def export_dataset(
        self,
        dataset: RLHFDataset,
        format: str = "json",
        file_path: Optional[str] = None
    ) -> str:
        """
        Export RLHF dataset to file.
        
        Args:
            dataset: RLHF dataset to export
            format: Export format (json, csv)
            file_path: Optional file path
            
        Returns:
            File path of exported dataset
        """
        try:
            if not file_path:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                file_path = f"./data/rlhf_dataset_{timestamp}.{format}"
            
            if format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(dataset.to_json())
            elif format.lower() == "csv":
                import pandas as pd
                
                # Convert to DataFrame
                data = []
                for point in dataset.data_points:
                    row = {
                        'user_input': point.user_input,
                        'agent_response': point.agent_response,
                        'feedback_score': point.human_feedback_score,
                        'quality_category': point.quality_category.value,
                        'interaction_id': point.interaction_id,
                        'timestamp': point.timestamp.isoformat()
                    }
                    # Add metadata as separate columns
                    for key, value in point.feedback_metadata.items():
                        row[f'metadata_{key}'] = value
                    data.append(row)
                
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"RLHF dataset exported to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to export dataset: {e}")
            raise
    
    async def get_rlhf_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get RLHF-related metrics and statistics."""
        try:
            dataset = await self.process_feedback_for_rlhf(days=days)
            
            metrics = {
                'total_datapoints': len(dataset),
                'quality_distribution': dataset.get_quality_distribution(),
                'average_feedback_score': dataset.get_average_score(),
                'dataset_metadata': dataset.metadata,
                'quality_percentages': {}
            }
            
            # Calculate quality percentages
            total = len(dataset)
            if total > 0:
                for quality, count in metrics['quality_distribution'].items():
                    metrics['quality_percentages'][quality] = round((count / total) * 100, 2)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get RLHF metrics: {e}")
            raise


# Global RLHF processor instance
rlhf_processor = RLHFProcessor()
