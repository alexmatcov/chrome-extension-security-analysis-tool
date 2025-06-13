const fs = require('fs').promises;
const path = require('path');
const https = require('https');
const http = require('http');

class EnhancedCRXCrawler {
    constructor(options = {}) {
        // MAXIMUM SPEED OPTIMIZATIONS:
        // - Direct API calls only (no browser overhead)
        // - 12x concurrency (12 vs 2 concurrent downloads)
        // - 12x faster delays (500ms vs 6s between requests)
        // - No page timeouts or browser management
        // - Expected speed improvement: ~20-30x faster crawling
        
        this.downloadDir = options.downloadDir || './downloads/crx_extensions';
        this.concurrency = options.concurrency || 12; // Increased from 2 to 12
        this.delayBetweenRequests = options.delayBetweenRequests || 500; // Reduced from 6000ms to 500ms
        this.retryAttempts = options.retryAttempts || 2; // Reduced from 3 to 2
        this.downloadTimeout = options.downloadTimeout || 45000; // Reduced from 180000ms to 45000ms
        this.userAgent = options.userAgent || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
        
        // Single download strategy - Direct API only
        this.downloadStrategies = [
            'directapi'
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
        
        this.checkpointInterval = 50; // Reduced from 100 to 50 for more frequent saves in fast mode
    }

    async initialize() {
        console.log('🚀 Initializing High-Speed Direct API CRX Crawler...');
        console.log(`📊 Target: ${this.stats.total} extensions`);
        console.log(`⚙️  Settings: ${this.concurrency} concurrent, ${this.delayBetweenRequests}ms delay`);
        console.log(`🔄 Strategy: Direct API Only (fastest method)`);
        console.log(`🏎️  MAXIMUM SPEED MODE: Direct downloads without browser overhead`);
        
        // No browser needed for direct API calls - maximum performance!
        console.log('✅ Direct API crawler initialized successfully (no browser overhead)');
    }

    async close() {
        // No browser to close - direct API only
        console.log('🔒 Direct API crawler finished');
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

            // Use Direct API strategy only
            try {
                console.log(`🔄 Using Direct API for ${extensionId}`);
                const result = await this.downloadViaDirectAPI(extensionId);
                
                if (result.success) {
                    const duration = Date.now() - startTime;
                    console.log(`✅ Downloaded ${extensionId} via Direct API (${Math.round(result.size/1024)}KB, ${duration}ms)`);
                    this.stats.completed++;
                    this.updateStrategyStats('directapi', 'success');
                    
                    return {
                        extensionId,
                        status: 'success',
                        strategy: 'directapi',
                        filepath: result.filepath,
                        size: result.size,
                        duration
                    };
                } else {
                    console.log(`❌ Direct API failed for ${extensionId}: ${result.error}`);
                    this.updateStrategyStats('directapi', 'failed');
                }
            } catch (error) {
                console.log(`❌ Direct API error for ${extensionId}: ${error.message}`);
                this.updateStrategyStats('directapi', 'error');
            }
            
            // Direct API failed
            console.log(`🔍 Extension not found: ${extensionId} - Direct API failed`);
            this.stats.notFound++;
            
            return {
                extensionId,
                status: 'not_found',
                error: 'Direct API download failed',
                duration: Date.now() - startTime
            };
            
        } catch (error) {
            const duration = Date.now() - startTime;
            console.log(`❌ Failed ${extensionId}: ${error.message} (${duration}ms)`);
            
            if (attempt < this.retryAttempts) {
                const retryDelay = Math.min(2000 * attempt, 8000); // Reduced from 5000 to 2000, max reduced from 15000 to 8000
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

    async downloadViaDirectAPI(extensionId) {
        // Try multiple API endpoints for maximum compatibility
        const apiUrls = [
            `https://clients2.google.com/service/update2/crx?response=redirect&os=win&arch=x86-64&nacl_arch=x86-64&prod=chromiumcrx&prodchannel=stable&prodversion=120.0.0.0&acceptformat=crx2,crx3&x=id%3D${extensionId}%26uc`,
            `https://clients2.google.com/service/update2/crx?response=redirect&prodversion=120.0.0.0&x=id=${extensionId}&uc`,
            `https://clients2.google.com/service/update2/crx?response=redirect&os=linux&arch=x86-64&prod=chromiumcrx&prodchannel=unknown&prodversion=120.0.0.0&x=id=${extensionId}&uc`,
            `https://edge.microsoft.com/extensionwebstorebase/v1/crx?response=redirect&x=id=${extensionId}&uc`
        ];

        for (const url of apiUrls) {
            try {
                console.log(`🌐 Trying API endpoint: ${url.includes('edge.microsoft') ? 'Microsoft Edge' : 'Google Chrome'}`);
                const downloadResult = await this.downloadFileDirectly(url, extensionId);
                if (downloadResult.success) {
                    return downloadResult;
                }
            } catch (error) {
                console.log(`❌ API endpoint failed: ${error.message}`);
            }
        }

        return { success: false, error: 'All direct API endpoints failed' };
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
        
        const report = {
            crawl_info: {
                timestamp: new Date().toISOString(),
                duration_ms: duration,
                duration_formatted: this.formatDuration(duration),
                extensions_targeted: this.stats.total,
                success_rate: ((successful.length / this.stats.total) * 100).toFixed(2) + '%',
                crawler_mode: 'DIRECT-API-ONLY'
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
                strategy_used: 'Direct API Only',
                strategy_stats: this.stats.strategyStats,
                api_endpoints_tested: 4
            },
            performance: {
                avg_download_time_ms: successful.length > 0 ?
                    Math.round(successful.reduce((sum, r) => sum + (r.duration || 0), 0) / successful.length) : 0,
                extensions_per_hour: Math.round((this.stats.total / duration) * 3600000),
                total_data_downloaded_mb: Math.round(successful.reduce((sum, r) => sum + (r.size || 0), 0) / 1024 / 1024),
                speed_mode: 'DIRECT-API-MAXIMUM'
            },
            breakdown: {
                successful_extensions: successful.map(r => ({ 
                    id: r.extensionId, 
                    strategy: 'directapi',
                    size_kb: Math.round((r.size || 0) / 1024) 
                })),
                not_found_extensions: notFound.map(r => ({ id: r.extensionId, error: r.error })),
                failed_extensions: failed.map(r => ({ id: r.extensionId, error: r.error }))
            }
        };
        
        const reportFile = path.join(this.downloadDir, 'direct_api_crawl_report.json');
        await fs.writeFile(reportFile, JSON.stringify(report, null, 2));
        
        const resultsFile = path.join(this.downloadDir, 'results.json');
        await fs.writeFile(resultsFile, JSON.stringify(results, null, 2));
        
        // Console summary
        console.log('\n' + '='.repeat(60));
        console.log('🏎️  DIRECT API MAXIMUM SPEED CRAWL REPORT');
        console.log('='.repeat(60));
        console.log(`⏱️  Duration: ${this.formatDuration(duration)}`);
        console.log(`📈 Success Rate: ${report.crawl_info.success_rate}`);
        console.log(`✅ Downloaded: ${successful.length} extensions`);
        console.log(`🔍 Not Found: ${notFound.length} extensions`);
        console.log(`❌ Failed: ${failed.length} extensions`);
        console.log(`⏭️  Skipped: ${skipped.length} extensions`);
        console.log(`💾 Total Data: ${report.performance.total_data_downloaded_mb} MB`);
        console.log(`🚀 Rate: ${report.performance.extensions_per_hour} extensions/hour`);
        console.log(`🔧 Strategy: Direct API Only (4 endpoints tested per extension)`);
        console.log(`📄 Report: ${reportFile}`);
        console.log('='.repeat(60));
    }

    async processBatch(extensionIds) {
        const results = [];
        let batchNumber = 1;
        
        for (let i = 0; i < extensionIds.length; i += this.concurrency) {
            const batch = extensionIds.slice(i, i + this.concurrency);
            const totalBatches = Math.ceil(extensionIds.length / this.concurrency);
            
            console.log(`\n📦 Batch ${batchNumber}/${totalBatches} (${batch.length} extensions)`);
            console.log(`📍 Progress: ${i}/${extensionIds.length} (${((i/extensionIds.length)*100).toFixed(1)}%)`);
            
            const batchPromises = batch.map(async (extensionId, index) => {
                // Reduced stagger time for faster processing
                await this.sleep(index * 200); // Reduced from 1000ms to 200ms
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
        console.log(`🚀 Starting Maximum Speed Direct API CRX Crawler`);
        console.log(`📊 Target: ${extensionIds.length} extensions`);
        console.log(`📁 Output: ${this.downloadDir}`);
        console.log(`⚙️  Config: ${this.concurrency} concurrent, ${this.delayBetweenRequests}ms delay`);
        console.log(`🔄 Strategy: Direct API Only (maximum speed)`);
        console.log(`🏎️  MAXIMUM SPEED MODE: ~20-30x faster performance (no browser overhead)\n`);
        
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
            stats: { ...this.stats },
            mode: 'DIRECT-API-ONLY'
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
            const lines = content.split('\n').map(line => line.trim()).filter(line => line);
            
            if (lines.length === 0) {
                throw new Error('CSV file is empty');
            }
            
            // Parse CSV header to find Extension_ID column
            const headers = this.parseCSVLine(lines[0]);
            console.log(`📋 CSV Headers found: ${headers.join(', ')}`);
            
            const extensionIdIndex = headers.findIndex(header => 
                header.toLowerCase().includes('extension_id') || 
                header.toLowerCase().includes('extensionid') ||
                header.toLowerCase() === 'id'
            );
            
            if (extensionIdIndex === -1) {
                console.log('⚠️  Extension_ID column not found. Available columns:', headers);
                console.log('🔍 Trying first column as fallback...');
                // Fallback to first column
                ids = lines.slice(1).map(line => {
                    const columns = this.parseCSVLine(line);
                    return columns[0] ? columns[0].trim() : '';
                }).filter(id => id);
            } else {
                console.log(`✅ Found Extension_ID column at index ${extensionIdIndex}: "${headers[extensionIdIndex]}"`);
                
                // Extract extension IDs from the correct column
                ids = lines.slice(1).map(line => {
                    const columns = this.parseCSVLine(line);
                    return columns[extensionIdIndex] ? columns[extensionIdIndex].trim() : '';
                }).filter(id => id);
            }
            
            console.log(`📊 Extracted ${ids.length} extension IDs from CSV`);
            
            // Show first few IDs for verification
            if (ids.length > 0) {
                console.log(`🔍 First 5 extension IDs: ${ids.slice(0, 5).join(', ')}`);
            }
            
        } else {
            // Plain text file (one ID per line)
            ids = content.split('\n')
                .map(line => line.trim())
                .filter(line => line && !line.startsWith('#'));
        }
        
        // Clean and validate extension IDs
        ids = ids.map(id => {
            // Remove quotes if present
            return id.replace(/^["']|["']$/g, '').trim();
        });
        
        const validIds = ids.filter(id => /^[a-p]{32}$/.test(id));
        const invalidIds = ids.filter(id => !/^[a-p]{32}$/.test(id));
        
        if (invalidIds.length > 0) {
            console.log(`⚠️  Found ${invalidIds.length} invalid extension IDs`);
            if (invalidIds.length <= 10) {
                console.log('❌ Invalid IDs:', invalidIds);
            } else {
                console.log('❌ Sample invalid IDs:', invalidIds.slice(0, 10));
            }
        }
        
        if (validIds.length === 0) {
            throw new Error('No valid extension IDs found in the file');
        }
        
        console.log(`✅ Loaded ${validIds.length} valid extension IDs out of ${ids.length} total entries`);
        console.log(`📈 Validation success rate: ${((validIds.length / ids.length) * 100).toFixed(1)}%`);
        
        return validIds;
    }

    // Helper method to parse CSV lines correctly (handles quotes and commas)
    parseCSVLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            
            if (char === '"') {
                if (inQuotes && line[i + 1] === '"') {
                    // Escaped quote
                    current += '"';
                    i++; // Skip next quote
                } else {
                    // Toggle quote state
                    inQuotes = !inQuotes;
                }
            } else if (char === ',' && !inQuotes) {
                // End of field
                result.push(current);
                current = '';
            } else {
                current += char;
            }
        }
        
        // Add the last field
        result.push(current);
        
        return result;
    }
}

// CLI usage - Optimized for maximum speed with Direct API only
async function main() {
    const crawler = new EnhancedCRXCrawler({
        downloadDir: './downloads/crx_extensions',
        concurrency: 12, // Maximum concurrent downloads
        delayBetweenRequests: 500, // Minimal delays
        retryAttempts: 2,
        downloadTimeout: 45000
    });

    try {
        // Load extension IDs from text file (original behavior)
        const txtPath = './extension_ids.txt';
        console.log(`📂 Loading extension IDs from: ${txtPath}`);
        console.log(`🚀 MAXIMUM SPEED MODE: Direct API only, 12 concurrent, 500ms delays`);
        
        const extensionIds = await crawler.loadExtensionIds(txtPath);
        
        console.log(`🎯 Target: ${extensionIds.length} extensions`);
        console.log(`📁 Output directory: ./downloads/crx_extensions`);
        
        // Ultra-optimistic time estimate for direct API mode
        const estimatedMinutes = Math.ceil((extensionIds.length * 8) / 60); // Reduced from 15s to 8s per extension
        console.log(`⏱️  Estimated completion time: ${estimatedMinutes} minutes (DIRECT API MODE)\n`);
        
        // Start crawl
        await crawler.crawl(extensionIds);
        
        console.log('\n🎉 Maximum speed Direct API extension crawl completed successfully!');
        console.log('📊 Check the direct_api_crawl_report.json for detailed analysis');
        
    } catch (error) {
        console.error('❌ Crawl failed:', error);
        
        // Provide helpful error messages for common issues
        if (error.message.includes('ENOENT')) {
            console.log('\n🔧 File not found. Please check:');
            console.log('   • The extension_ids.txt file exists in the current directory');
            console.log('   • You\'re running the script from the correct directory');
            console.log('   • The file contains valid Chrome extension IDs (32 characters each)');
            console.log('\n💡 Expected format in extension_ids.txt:');
            console.log('   gjaokfmjhbebkhkjmkbljemcbnjeiogl');
            console.log('   cjpalhdlnbpafiamejdnhcphjbkeiagm');
            console.log('   hdokiejnpimakedhajhdlcegeplioahd');
        } else if (error.message.includes('No valid extension IDs found')) {
            console.log('\n🔧 Extension ID validation issue:');
            console.log('   • Check that extension_ids.txt contains valid 32-character extension IDs');
            console.log('   • Extension IDs should only contain letters a-p');
            console.log('   • One extension ID per line');
            console.log('   • Remove any extra spaces or characters');
        }
        
        process.exit(1);
    }
}

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n⚠️  Received interrupt signal. Closing browser gracefully...');
    process.exit(0);
});

module.exports = EnhancedCRXCrawler;

if (require.main === module) {
    main();
}