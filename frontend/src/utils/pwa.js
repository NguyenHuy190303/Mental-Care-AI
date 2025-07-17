/**
 * Progressive Web App utilities for Mental Health Agent
 * Handles PWA installation, offline support, and mobile features
 */

class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.isOnline = navigator.onLine;
        this.serviceWorker = null;
        
        this.init();
    }
    
    async init() {
        // Register service worker
        await this.registerServiceWorker();
        
        // Set up PWA install prompt
        this.setupInstallPrompt();
        
        // Set up offline/online detection
        this.setupConnectionMonitoring();
        
        // Set up push notifications
        this.setupPushNotifications();
        
        // Check if already installed
        this.checkInstallStatus();
        
        // Set up background sync
        this.setupBackgroundSync();
    }
    
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                this.serviceWorker = registration;
                
                console.log('Service Worker registered successfully');
                
                // Handle service worker updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New version available
                            this.showUpdateAvailable();
                        }
                    });
                });
                
                // Listen for messages from service worker
                navigator.serviceWorker.addEventListener('message', this.handleServiceWorkerMessage.bind(this));
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }
    
    setupInstallPrompt() {
        // Listen for beforeinstallprompt event
        window.addEventListener('beforeinstallprompt', (e) => {
            // Prevent the mini-infobar from appearing
            e.preventDefault();
            
            // Store the event for later use
            this.deferredPrompt = e;
            
            // Show custom install button
            this.showInstallButton();
        });
        
        // Listen for app installed event
        window.addEventListener('appinstalled', () => {
            console.log('PWA was installed');
            this.isInstalled = true;
            this.hideInstallButton();
            this.trackInstallation();
        });
    }
    
    setupConnectionMonitoring() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.handleOnline();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.handleOffline();
        });
    }
    
    async setupPushNotifications() {
        if ('Notification' in window && 'serviceWorker' in navigator) {
            // Request notification permission
            const permission = await this.requestNotificationPermission();
            
            if (permission === 'granted') {
                await this.subscribeToPushNotifications();
            }
        }
    }
    
    checkInstallStatus() {
        // Check if running as PWA
        if (window.matchMedia('(display-mode: standalone)').matches || 
            window.navigator.standalone === true) {
            this.isInstalled = true;
        }
    }
    
    setupBackgroundSync() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            // Background sync is supported
            console.log('Background sync is supported');
        }
    }
    
    // Install PWA
    async installPWA() {
        if (!this.deferredPrompt) {
            console.log('Install prompt not available');
            return false;
        }
        
        try {
            // Show the install prompt
            this.deferredPrompt.prompt();
            
            // Wait for user response
            const { outcome } = await this.deferredPrompt.userChoice;
            
            if (outcome === 'accepted') {
                console.log('User accepted the install prompt');
                this.trackInstallation();
            } else {
                console.log('User dismissed the install prompt');
            }
            
            // Clear the deferred prompt
            this.deferredPrompt = null;
            
            return outcome === 'accepted';
            
        } catch (error) {
            console.error('Error during PWA installation:', error);
            return false;
        }
    }
    
    // Show install button
    showInstallButton() {
        const installButton = document.getElementById('pwa-install-button');
        if (installButton) {
            installButton.style.display = 'block';
            installButton.addEventListener('click', () => this.installPWA());
        } else {
            // Create install button if it doesn't exist
            this.createInstallButton();
        }
    }
    
    hideInstallButton() {
        const installButton = document.getElementById('pwa-install-button');
        if (installButton) {
            installButton.style.display = 'none';
        }
    }
    
    createInstallButton() {
        const button = document.createElement('button');
        button.id = 'pwa-install-button';
        button.innerHTML = '📱 Install App';
        button.className = 'pwa-install-btn';
        button.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #3b82f6;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
            z-index: 1000;
            transition: all 0.3s ease;
        `;
        
        button.addEventListener('mouseover', () => {
            button.style.transform = 'translateY(-2px)';
            button.style.boxShadow = '0 6px 16px rgba(59, 130, 246, 0.4)';
        });
        
        button.addEventListener('mouseout', () => {
            button.style.transform = 'translateY(0)';
            button.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
        });
        
        button.addEventListener('click', () => this.installPWA());
        
        document.body.appendChild(button);
    }
    
    // Handle online/offline events
    handleOnline() {
        console.log('Connection restored');
        
        // Show online notification
        this.showNotification('Connection Restored', {
            body: 'You are back online. Syncing data...',
            icon: '/icons/icon-192x192.png',
            tag: 'connection-status'
        });
        
        // Trigger background sync
        this.triggerBackgroundSync();
        
        // Update UI
        this.updateConnectionStatus(true);
    }
    
    handleOffline() {
        console.log('Connection lost');
        
        // Show offline notification
        this.showNotification('You are Offline', {
            body: 'Emergency resources are still available',
            icon: '/icons/icon-192x192.png',
            tag: 'connection-status',
            actions: [
                {
                    action: 'emergency',
                    title: 'Emergency Help'
                }
            ]
        });
        
        // Update UI
        this.updateConnectionStatus(false);
    }
    
    updateConnectionStatus(isOnline) {
        // Update connection indicator in UI
        const indicator = document.querySelector('.connection-indicator');
        if (indicator) {
            indicator.className = `connection-indicator ${isOnline ? 'online' : 'offline'}`;
            indicator.textContent = isOnline ? 'Online' : 'Offline';
        }
        
        // Dispatch custom event
        window.dispatchEvent(new CustomEvent('connectionchange', {
            detail: { isOnline }
        }));
    }
    
    // Push notifications
    async requestNotificationPermission() {
        if (!('Notification' in window)) {
            console.log('This browser does not support notifications');
            return 'denied';
        }
        
        if (Notification.permission === 'granted') {
            return 'granted';
        }
        
        if (Notification.permission !== 'denied') {
            const permission = await Notification.requestPermission();
            return permission;
        }
        
        return Notification.permission;
    }
    
    async subscribeToPushNotifications() {
        if (!this.serviceWorker) {
            console.log('Service worker not available');
            return;
        }
        
        try {
            const subscription = await this.serviceWorker.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(process.env.REACT_APP_VAPID_PUBLIC_KEY)
            });
            
            // Send subscription to server
            await this.sendSubscriptionToServer(subscription);
            
            console.log('Push notification subscription successful');
            
        } catch (error) {
            console.error('Failed to subscribe to push notifications:', error);
        }
    }
    
    async sendSubscriptionToServer(subscription) {
        try {
            const response = await fetch('/api/notifications/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify(subscription)
            });
            
            if (!response.ok) {
                throw new Error('Failed to send subscription to server');
            }
            
        } catch (error) {
            console.error('Error sending subscription to server:', error);
        }
    }
    
    // Show notification
    async showNotification(title, options = {}) {
        if ('Notification' in window && Notification.permission === 'granted') {
            if ('serviceWorker' in navigator && this.serviceWorker) {
                // Use service worker to show notification
                await this.serviceWorker.showNotification(title, options);
            } else {
                // Fallback to regular notification
                new Notification(title, options);
            }
        }
    }
    
    // Background sync
    async triggerBackgroundSync() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            try {
                await this.serviceWorker.sync.register('sync-messages');
                await this.serviceWorker.sync.register('sync-feedback');
                console.log('Background sync registered');
            } catch (error) {
                console.error('Background sync registration failed:', error);
            }
        }
    }
    
    // Handle service worker messages
    handleServiceWorkerMessage(event) {
        const { data } = event;
        
        switch (data.type) {
            case 'CACHE_UPDATED':
                console.log('Cache updated');
                break;
            case 'SYNC_COMPLETE':
                console.log('Background sync completed');
                break;
            case 'EMERGENCY_ACCESS':
                this.trackEmergencyAccess(data);
                break;
            default:
                console.log('Unknown service worker message:', data);
        }
    }
    
    // Show update available notification
    showUpdateAvailable() {
        const updateBanner = document.createElement('div');
        updateBanner.id = 'update-banner';
        updateBanner.innerHTML = `
            <div style="background: #3b82f6; color: white; padding: 12px; text-align: center; position: fixed; top: 0; left: 0; right: 0; z-index: 10000;">
                <span>A new version is available!</span>
                <button onclick="pwaManager.updateApp()" style="background: white; color: #3b82f6; border: none; padding: 4px 12px; margin-left: 12px; border-radius: 4px; cursor: pointer;">Update</button>
                <button onclick="this.parentElement.parentElement.remove()" style="background: transparent; color: white; border: 1px solid white; padding: 4px 12px; margin-left: 8px; border-radius: 4px; cursor: pointer;">Later</button>
            </div>
        `;
        
        document.body.appendChild(updateBanner);
    }
    
    // Update app
    async updateApp() {
        if (this.serviceWorker && this.serviceWorker.waiting) {
            // Tell the waiting service worker to skip waiting
            this.serviceWorker.waiting.postMessage({ type: 'SKIP_WAITING' });
            
            // Reload the page
            window.location.reload();
        }
    }
    
    // Utility functions
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        
        return outputArray;
    }
    
    // Analytics and tracking
    trackInstallation() {
        // Track PWA installation
        if (window.gtag) {
            window.gtag('event', 'pwa_install', {
                event_category: 'PWA',
                event_label: 'Installation'
            });
        }
        
        // Send to backend analytics
        fetch('/api/analytics/pwa-install', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                timestamp: new Date().toISOString(),
                user_agent: navigator.userAgent
            })
        }).catch(error => {
            console.error('Failed to track installation:', error);
        });
    }
    
    trackEmergencyAccess(data) {
        // Track emergency resource access
        fetch('/api/analytics/emergency-access', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                timestamp: data.timestamp,
                offline: !this.isOnline,
                source: 'pwa'
            })
        }).catch(error => {
            console.error('Failed to track emergency access:', error);
        });
    }
    
    // Mobile-specific features
    setupMobileFeatures() {
        // Prevent zoom on input focus (iOS)
        if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
            const viewport = document.querySelector('meta[name=viewport]');
            if (viewport) {
                viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
            }
        }
        
        // Handle safe area insets
        if (CSS.supports('padding-top: env(safe-area-inset-top)')) {
            document.documentElement.style.setProperty('--safe-area-inset-top', 'env(safe-area-inset-top)');
            document.documentElement.style.setProperty('--safe-area-inset-bottom', 'env(safe-area-inset-bottom)');
        }
        
        // Vibration API for crisis alerts
        if ('vibrate' in navigator) {
            this.vibrationSupported = true;
        }
    }
    
    // Crisis vibration pattern
    crisisVibration() {
        if (this.vibrationSupported) {
            navigator.vibrate([300, 100, 300, 100, 300]);
        }
    }
    
    // Get device info
    getDeviceInfo() {
        return {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine,
            screenWidth: screen.width,
            screenHeight: screen.height,
            windowWidth: window.innerWidth,
            windowHeight: window.innerHeight,
            devicePixelRatio: window.devicePixelRatio,
            touchSupport: 'ontouchstart' in window,
            standalone: window.navigator.standalone || window.matchMedia('(display-mode: standalone)').matches
        };
    }
}

// Initialize PWA manager
const pwaManager = new PWAManager();

// Export for global use
window.pwaManager = pwaManager;

export default pwaManager;
