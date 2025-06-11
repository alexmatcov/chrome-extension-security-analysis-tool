const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');
const https = require('https');
const http = require('http');

class EnhancedCRXCrawler {
    constructor(options = {}) {
        this.downloadDir = options.downloadDir || './downloads/crx_extensions';
        this.concurrency = options.concurrency || 2;
        this.delayBetweenRequests = options.delayBetweenRequests || 6000;
        this.retryAttempts = options.retryAttempts || 3;
        this.headless = options.headless !== false;
        this.pageTimeout = options.pageTimeout || 90000;
        this.downloadTimeout = options.downloadTimeout || 180000;
        this.userAgent = options.userAgent || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
        
        // Multiple download strategies
        this.downloadStrategies = [
            'crxviewer',
            'directapi',
            'crxextractor',
            'crxviewer_com'
        ];
        
        this.stats = {
            total: 0,
            completed: 0,
            failed: 0,
            notFound: 0,
            skipped: 0,
            startTime: null,
            lastCheckpoint: 0,
            strategyStats: {}
        };
        
        this.browser = null;
        this.checkpointInterval = 100;
    }

    async initialize() {
        console.log('🚀 Initializing Enhanced CRX Crawler...');
        console.log(`📊 Target: ${this.stats.total} extensions`);
        console.log(`⚙️  Settings: ${this.concurrency} concurrent, ${this.delayBetweenRequests}ms delay`);
        console.log(`🔄 Strategies: ${this.downloadStrategies.join(', ')}`);
        
        this.browser = await puppeteer.launch({
            headless: this.headless,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-blink-features=AutomationControlled'
            ],
            defaultViewport: { width: 1280, height: 720 }
        });
        
        console.log('✅ Browser initialized successfully');
    }

    async close() {
        if (this.browser) {
            await this.browser.close();
            console.log('🔒 Browser closed');
        }
    }

    async downloadExtension(extensionId, attempt = 1) {
        const startTime = Date.now();
        console.log(`📥 [${attempt}/${this.retryAttempts}] Processing ${extensionId}...`);
        
        try {
            // Check if already downloaded
            const expectedFile = path.join(this.downloadDir, `${extensionId}.zip`);
            try {
                const stats = await fs.stat(expectedFile);
                if (stats.size > 1000) {
                    console.log(`⏭️  Skipping ${extensionId} (already exists, ${Math.round(stats.size/1024)}KB)`);
                    this.stats.skipped++;
                    return { extensionId, status: 'skipped', filepath: expectedFile, size: stats.size };
                }
            } catch (err) {
                // File doesn't exist, proceed with download
            }

            // Try each strategy until one works
            for (const strategy of this.downloadStrategies) {
                try {
                    console.log(`🔄 Trying strategy: ${strategy} for ${extensionId}`);
                    const result = await this.tryDownloadStrategy(strategy, extensionId);
                    
                    if (result.success) {
                        const duration = Date.now() - startTime;
                        console.log(`✅ Downloaded ${extensionId} via ${strategy} (${Math.round(result.size/1024)}KB, ${duration}ms)`);
                        this.stats.completed++;
                        this.updateStrategyStats(strategy, 'success');
                        
                        return {
                            extensionId,
                            status: 'success',
                            strategy: strategy,
                            filepath: result.filepath,
                            size: result.size,
                            duration
                        };
                    } else {
                        console.log(`❌ Strategy ${strategy} failed for ${extensionId}: ${result.error}`);
                        this.updateStrategyStats(strategy, 'failed');
                    }
                } catch (error) {
                    console.log(`❌ Strategy ${strategy} error for ${extensionId}: ${error.message}`);
                    this.updateStrategyStats(strategy, 'error');
                }
                
                // Small delay between strategies
                await this.sleep(2000);
            }
            
            // All strategies failed
            console.log(`🔍 Extension not found: ${extensionId} - All strategies failed`);
            this.stats.notFound++;
            
            return {
                extensionId,
                status: 'not_found',
                error: 'All download strategies failed',
                duration: Date.now() - startTime
            };
            
        } catch (error) {
            const duration = Date.now() - startTime;
            console.log(`❌ Failed ${extensionId}: ${error.message} (${duration}ms)`);
            
            if (attempt < this.retryAttempts) {
                const retryDelay = Math.min(5000 * attempt, 15000);
                console.log(`🔄 Retrying ${extensionId} in ${retryDelay}ms...`);
                await this.sleep(retryDelay);
                return this.downloadExtension(extensionId, attempt + 1);
            } else {
                this.stats.failed++;
                return {
                    extensionId,
                    status: 'failed',
                    error: error.message,
                    duration
                };
            }
        }
    }

    async tryDownloadStrategy(strategy, extensionId) {
        switch (strategy) {
            case 'crxviewer':
                return await this.downloadViaCRXViewer(extensionId);
            case 'directapi':
                return await this.downloadViaDirectAPI(extensionId);
            case 'crxextractor':
                return await this.downloadViaCRXExtractor(extensionId);
            case 'crxviewer_com':
                return await this.downloadViaCRXViewerCom(extensionId);
            default:
                throw new Error(`Unknown strategy: ${strategy}`);
        }
    }

    async downloadViaCRXViewer(extensionId) {
        const page = await this.browser.newPage();
        
        try {
            await page.setUserAgent(this.userAgent);
            await page.setDefaultTimeout(this.pageTimeout);

            // Navigate to CRX Viewer
            await page.goto('https://robwu.nl/crxviewer/', { 
                waitUntil: 'networkidle0',
                timeout: this.pageTimeout 
            });

            // Enter extension ID
            const inputSelector = 'input[name="xid"]';
            await page.waitForSelector(inputSelector, { timeout: 10000 });
            
            await page.click(inputSelector);
            await page.keyboard.down('Control');
            await page.keyboard.press('a');
            await page.keyboard.up('Control');
            await page.type(inputSelector, extensionId, { delay: 50 });
            
            // Submit form
            await page.keyboard.press('Enter');
            
            // Wait for result with improved error handling
            const result = await this.waitForCRXViewerResult(page, extensionId);
            
            if (result.success && result.downloadUrl) {
                const downloadResult = await this.downloadFileFromBlob(result.downloadUrl, extensionId);
                return { success: true, ...downloadResult };
            } else {
                return { success: false, error: result.error || 'No download link found' };
            }
            
        } finally {
            await page.close();
        }
    }

    async downloadViaDirectAPI(extensionId) {
        // Try multiple API endpoints
        const apiUrls = [
            `https://clients2.google.com/service/update2/crx?response=redirect&os=win&arch=x86-64&nacl_arch=x86-64&prod=chromiumcrx&prodchannel=stable&prodversion=120.0.0.0&acceptformat=crx2,crx3&x=id%3D${extensionId}%26uc`,
            `https://clients2.google.com/service/update2/crx?response=redirect&prodversion=120.0.0.0&x=id=${extensionId}&uc`,
            `https://edge.microsoft.com/extensionwebstorebase/v1/crx?response=redirect&x=id=${extensionId}&uc`
        ];

        for (const url of apiUrls) {
            try {
                const downloadResult = await this.downloadFileDirectly(url, extensionId);
                if (downloadResult.success) {
                    return downloadResult;
                }
            } catch (error) {
                console.log(`Direct API failed for ${url}: ${error.message}`);
            }
        }

        return { success: false, error: 'All direct API endpoints failed' };
    }

    async downloadViaCRXExtractor(extensionId) {
        const page = await this.browser.newPage();
        
        try {
            await page.setUserAgent(this.userAgent);
            
            // Navigate to CRXExtractor.com
            await page.goto('https://crxextractor.com/', { 
                waitUntil: 'networkidle0',
                timeout: this.pageTimeout 
            });

            // Enter Chrome Web Store URL
            const chromeStoreUrl = `https://chrome.google.com/webstore/detail/${extensionId}`;
            const inputSelector = 'input[type="text"], input[name="url"], #url';
            
            await page.waitForSelector(inputSelector, { timeout: 10000 });
            await page.type(inputSelector, chromeStoreUrl);
            
            // Click submit/OK button
            const submitButton = await page.$('button:contains("OK"), input[type="submit"], .btn');
            if (submitButton) {
                await submitButton.click();
            }
            
            // Wait for download link
            await page.waitForSelector('a[download], a[href$=".crx"], a[href$=".zip"]', { timeout: 30000 });
            
            const downloadLink = await page.$eval('a[download], a[href$=".crx"], a[href$=".zip"]', el => el.href);
            
            if (downloadLink) {
                const downloadResult = await this.downloadFileDirectly(downloadLink, extensionId);
                return downloadResult;
            } else {
                return { success: false, error: 'No download link found on CRXExtractor' };
            }
            
        } finally {
            await page.close();
        }
    }

    async downloadViaCRXViewerCom(extensionId) {
        const page = await this.browser.newPage();
        
        try {
            await page.setUserAgent(this.userAgent);
            
            // Navigate to CRXViewer.com
            await page.goto('https://crxviewer.com/', { 
                waitUntil: 'networkidle0',
                timeout: this.pageTimeout 
            });

            // Enter extension ID or URL
            const chromeStoreUrl = `https://chrome.google.com/webstore/detail/${extensionId}`;
            const inputSelector = 'input[type="url"], input[name="url"], #url-input';
            
            await page.waitForSelector(inputSelector, { timeout: 10000 });
            await page.type(inputSelector, chromeStoreUrl);
            
            // Submit
            await page.keyboard.press('Enter');
            
            // Wait for download option
            await page.waitForSelector('a[download], .download-btn, button:contains("Download")', { timeout: 30000 });
            
            const downloadLink = await page.$eval('a[download], .download-btn', el => el.href);
            
            if (downloadLink) {
                const downloadResult = await this.downloadFileDirectly(downloadLink, extensionId);
                return downloadResult;
            } else {
                return { success: false, error: 'No download link found on CRXViewer.com' };
            }
            
        } finally {
            await page.close();
        }
    }

    async waitForCRXViewerResult(page, extensionId) {
        const maxWaitTime = 45000; // Increased timeout
        const startTime = Date.now();
        
        while (Date.now() - startTime < maxWaitTime) {
            try {
                // Check for download link (higher priority)
                const downloadLinkExists = await page.$('a[id="download-link"], a[download*=".zip"], a[href*="blob:"], a[title*="Download"], .download-button');
                
                if (downloadLinkExists) {
                    const downloadUrl = await page.evaluate((element) => {
                        return element.href;
                    }, downloadLinkExists);
                    
                    if (downloadUrl && (downloadUrl.startsWith('blob:') || downloadUrl.includes('.zip'))) {
                        return { success: true, downloadUrl };
                    }
                }
                
                // Check for upload option (fallback)
                const uploadOption = await page.$('input[type="file"], .file-upload, #file-input');
                if (uploadOption) {
                    // This means the extension needs to be uploaded manually
                    return { success: false, error: 'Extension requires manual upload' };
                }
                
                // Check for actual errors (ignore Google API failures)
                const errorText = await page.evaluate(() => {
                    const errorElements = document.querySelectorAll('.error, .alert-danger, .warning');
                    for (const el of errorElements) {
                        const text = el.textContent.toLowerCase();
                        if (text.includes('extension not found') || 
                            text.includes('invalid extension') || 
                            text.includes('404') ||
                            text.includes('not available')) {
                            return el.textContent;
                        }
                    }
                    return null;
                });
                
                if (errorText) {
                    return { success: false, error: errorText.trim() };
                }
                
                await this.sleep(2000);
                
            } catch (error) {
                // Continue trying
            }
        }
        
        return { success: false, error: 'Timeout waiting for CRX Viewer result' };
    }

    async downloadFileDirectly(url, extensionId) {
        return new Promise((resolve, reject) => {
            const filepath = path.join(this.downloadDir, `${extensionId}.zip`);
            const protocol = url.startsWith('https:') ? https : http;
            
            const request = protocol.get(url, {
                headers: {
                    'User-Agent': this.userAgent,
                    'Accept': 'application/octet-stream,*/*',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            }, (response) => {
                
                // Handle redirects
                if (response.statusCode >= 300 && response.statusCode < 400 && response.headers.location) {
                    this.downloadFileDirectly(response.headers.location, extensionId)
                        .then(resolve)
                        .catch(reject);
                    return;
                }
                
                if (response.statusCode !== 200) {
                    reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
                    return;
                }
                
                const fileStream = require('fs').createWriteStream(filepath);
                response.pipe(fileStream);
                
                fileStream.on('finish', async () => {
                    try {
                        const stats = await fs.stat(filepath);
                        if (stats.size < 1000) {
                            reject(new Error('Downloaded file too small'));
                        } else {
                            resolve({ success: true, filepath, size: stats.size });
                        }
                    } catch (error) {
                        reject(error);
                    }
                });
                
                fileStream.on('error', reject);
            });
            
            request.on('error', reject);
            request.setTimeout(this.downloadTimeout, () => {
                request.destroy();
                reject(new Error('Download timeout'));
            });
        });
    }

    async downloadFileFromBlob(blobUrl, extensionId) {
        const downloadPage = await this.browser.newPage();
        
        try {
            const expectedFilename = `${extensionId}.zip`;
            const filepath = path.join(this.downloadDir, expectedFilename);
            
            const response = await downloadPage.goto(blobUrl, { 
                waitUntil: 'networkidle0',
                timeout: this.downloadTimeout 
            });
            
            if (!response.ok()) {
                throw new Error(`Failed to fetch blob: ${response.status()}`);
            }
            
            const buffer = await response.buffer();
            await fs.writeFile(filepath, buffer);
            
            const stats = await fs.stat(filepath);
            
            if (stats.size < 1000) {
                throw new Error('Downloaded file is too small, likely an error');
            }
            
            return { filepath, size: stats.size };
            
        } finally {
            await downloadPage.close();
        }
    }

    updateStrategyStats(strategy, result) {
        if (!this.stats.strategyStats[strategy]) {
            this.stats.strategyStats[strategy] = { success: 0, failed: 0, error: 0 };
        }
        this.stats.strategyStats[strategy][result]++;
    }

    async generateFinalReport(results, duration) {
        const successful = results.filter(r => r.status === 'success');
        const notFound = results.filter(r => r.status === 'not_found');
        const failed = results.filter(r => r.status === 'failed');
        const skipped = results.filter(r => r.status === 'skipped');
        
        // Strategy analysis
        const strategyBreakdown = {};
        successful.forEach(r => {
            if (r.strategy) {
                strategyBreakdown[r.strategy] = (strategyBreakdown[r.strategy] || 0) + 1;
            }
        });
        
        const report = {
            crawl_info: {
                timestamp: new Date().toISOString(),
                duration_ms: duration,
                duration_formatted: this.formatDuration(duration),
                extensions_targeted: this.stats.total,
                success_rate: ((successful.length / this.stats.total) * 100).toFixed(2) + '%'
            },
            statistics: {
                successful_downloads: successful.length,
                extensions_not_found: notFound.length,
                failed_downloads: failed.length,
                skipped_existing: skipped.length,
                total_size_bytes: successful.reduce((sum, r) => sum + (r.size || 0), 0),
                avg_extension_size_kb: successful.length > 0 ? 
                    Math.round(successful.reduce((sum, r) => sum + (r.size || 0), 0) / successful.length / 1024) : 0
            },
            strategy_analysis: {
                strategy_breakdown: strategyBreakdown,
                strategy_stats: this.stats.strategyStats,
                most_effective_strategy: Object.keys(strategyBreakdown).reduce((a, b) => 
                    strategyBreakdown[a] > strategyBreakdown[b] ? a : b, '')
            },
            performance: {
                avg_download_time_ms: successful.length > 0 ?
                    Math.round(successful.reduce((sum, r) => sum + (r.duration || 0), 0) / successful.length) : 0,
                extensions_per_hour: Math.round((this.stats.total / duration) * 3600000),
                total_data_downloaded_mb: Math.round(successful.reduce((sum, r) => sum + (r.size || 0), 0) / 1024 / 1024)
            },
            breakdown: {
                successful_extensions: successful.map(r => ({ 
                    id: r.extensionId, 
                    strategy: r.strategy,
                    size_kb: Math.round((r.size || 0) / 1024) 
                })),
                not_found_extensions: notFound.map(r => ({ id: r.extensionId, error: r.error })),
                failed_extensions: failed.map(r => ({ id: r.extensionId, error: r.error }))
            }
        };
        
        const reportFile = path.join(this.downloadDir, 'enhanced_crawl_report.json');
        await fs.writeFile(reportFile, JSON.stringify(report, null, 2));
        
        const resultsFile = path.join(this.downloadDir, 'results.json');
        await fs.writeFile(resultsFile, JSON.stringify(results, null, 2));
        
        // Console summary
        console.log('\n' + '='.repeat(60));
        console.log('📊 ENHANCED CRAWL REPORT');
        console.log('='.repeat(60));
        console.log(`⏱️  Duration: ${this.formatDuration(duration)}`);
        console.log(`📈 Success Rate: ${report.crawl_info.success_rate}`);
        console.log(`✅ Downloaded: ${successful.length} extensions`);
        console.log(`🔍 Not Found: ${notFound.length} extensions`);
        console.log(`❌ Failed: ${failed.length} extensions`);
        console.log(`⏭️  Skipped: ${skipped.length} extensions`);
        console.log(`💾 Total Data: ${report.performance.total_data_downloaded_mb} MB`);
        console.log(`🚀 Rate: ${report.performance.extensions_per_hour} extensions/hour`);
        console.log(`🏆 Most Effective Strategy: ${report.strategy_analysis.most_effective_strategy}`);
        console.log(`📊 Strategy Breakdown:`);
        Object.entries(strategyBreakdown).forEach(([strategy, count]) => {
            console.log(`   ${strategy}: ${count} successful downloads`);
        });
        console.log(`📄 Report: ${reportFile}`);
        console.log('='.repeat(60));
    }

    // Copy the rest of your utility functions here...
    async processBatch(extensionIds) {
        const results = [];
        let batchNumber = 1;
        
        for (let i = 0; i < extensionIds.length; i += this.concurrency) {
            const batch = extensionIds.slice(i, i + this.concurrency);
            const totalBatches = Math.ceil(extensionIds.length / this.concurrency);
            
            console.log(`\n📦 Batch ${batchNumber}/${totalBatches} (${batch.length} extensions)`);
            console.log(`📍 Progress: ${i}/${extensionIds.length} (${((i/extensionIds.length)*100).toFixed(1)}%)`);
            
            const batchPromises = batch.map(async (extensionId, index) => {
                await this.sleep(index * 1000);
                const result = await this.downloadExtension(extensionId);
                this.printProgress();
                return result;
            });

            const batchResults = await Promise.all(batchPromises);
            results.push(...batchResults);
            
            if (results.length - this.stats.lastCheckpoint >= this.checkpointInterval) {
                await this.saveCheckpoint(results);
                this.stats.lastCheckpoint = results.length;
            }
            
            if (i + this.concurrency < extensionIds.length) {
                console.log(`⏸️  Inter-batch delay: ${this.delayBetweenRequests}ms`);
                await this.sleep(this.delayBetweenRequests);
            }
            
            batchNumber++;
        }

        return results;
    }

    async crawl(extensionIds) {
        console.log(`🚀 Starting Enhanced CRX Crawler`);
        console.log(`📊 Target: ${extensionIds.length} extensions`);
        console.log(`📁 Output: ${this.downloadDir}`);
        console.log(`⚙️  Config: ${this.concurrency} concurrent, ${this.delayBetweenRequests}ms delay`);
        console.log(`🔄 Strategies: ${this.downloadStrategies.join(', ')}\n`);
        
        await fs.mkdir(this.downloadDir, { recursive: true });
        
        this.stats.total = extensionIds.length;
        this.stats.startTime = Date.now();
        
        try {
            await this.initialize();
            const results = await this.processBatch(extensionIds);
            const endTime = Date.now();
            const duration = endTime - this.stats.startTime;
            await this.generateFinalReport(results, duration);
            return results;
        } catch (error) {
            console.error('❌ Critical crawler error:', error);
            throw error;
        } finally {
            await this.close();
        }
    }

    // Include all your utility functions (sleep, formatDuration, etc.)
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    formatDuration(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
        if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
        return `${seconds}s`;
    }

    printProgress() {
        const processed = this.stats.completed + this.stats.failed + this.stats.notFound + this.stats.skipped;
        const percentage = ((processed / this.stats.total) * 100).toFixed(1);
        const elapsed = Date.now() - this.stats.startTime;
        const rate = processed > 0 ? Math.round((processed / elapsed) * 3600000) : 0;
        
        process.stdout.write(`\r📊 ${processed}/${this.stats.total} (${percentage}%) | ✅ ${this.stats.completed} | 🔍 ${this.stats.notFound} | ❌ ${this.stats.failed} | ⏭️ ${this.stats.skipped} | 🚀 ${rate}/hr`);
    }

    async saveCheckpoint(results) {
        const checkpointFile = path.join(this.downloadDir, `checkpoint_${Date.now()}.json`);
        const checkpointData = {
            timestamp: new Date().toISOString(),
            processed: results.length,
            results: results,
            stats: { ...this.stats }
        };
        
        await fs.writeFile(checkpointFile, JSON.stringify(checkpointData, null, 2));
        console.log(`💾 Checkpoint saved: ${results.length} extensions processed`);
    }

    async loadExtensionIds(filepath) {
        console.log(`📂 Loading extension IDs from: ${filepath}`);
        
        const content = await fs.readFile(filepath, 'utf8');
        let ids = [];
        
        if (filepath.endsWith('.json')) {
            const data = JSON.parse(content);
            ids = Array.isArray(data) ? data : [data];
        } else if (filepath.endsWith('.csv')) {
            ids = content.split('\n')
                .slice(1)
                .map(line => line.split(',')[0].trim())
                .filter(id => id);
        } else {
            ids = content.split('\n')
                .map(line => line.trim())
                .filter(line => line && !line.startsWith('#'));
        }
        
        const validIds = ids.filter(id => /^[a-p]{32}$/.test(id));
        const invalidIds = ids.filter(id => !/^[a-p]{32}$/.test(id));
        
        if (invalidIds.length > 0) {
            console.log(`⚠️  Found ${invalidIds.length} invalid extension IDs`);
            if (invalidIds.length <= 10) {
                console.log('Invalid IDs:', invalidIds);
            }
        }
        
        console.log(`✅ Loaded ${validIds.length} valid extension IDs`);
        return validIds;
    }
}

// CLI usage
async function main() {
    const crawler = new EnhancedCRXCrawler({
        downloadDir: './downloads/crx_extensions',
        concurrency: 2,
        delayBetweenRequests: 6000,
        retryAttempts: 3,
        headless: true
    });

    try {
        const extensionIds = await crawler.loadExtensionIds('./extension_ids.txt');
        await crawler.crawl(extensionIds);
        console.log('\n🎉 Enhanced crawl completed successfully!');
    } catch (error) {
        console.error('❌ Crawl failed:', error);
        process.exit(1);
    }
}

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\nReceived interrupt signal. Closing browser gracefully...');
    process.exit(0);
});

module.exports = EnhancedCRXCrawler;

if (require.main === module) {
    main();
}