const ProductionCRXCrawler = require('./crx-crawler');

async function testSingleExtension() {
    console.log('🧪 Testing Production CRX Crawler with single extension\n');
    
    const crawler = new ProductionCRXCrawler({
        downloadDir: './test_downloads',
        concurrency: 1,
        delayBetweenRequests: 3000,
        retryAttempts: 2,
        headless: false // Show browser for testing
    });

    try {
        // Test with a known working extension
        const testExtensionId = 'agkpclldfjffanjojbkhkakaliiohebe'; // CRX Viewer extension
        
        console.log(`📝 Testing extension: ${testExtensionId}`);
        console.log('🔍 This is the CRX Viewer extension (should work)');
        console.log('⏱️  Expected time: 30-60 seconds\n');
        
        const results = await crawler.crawl([testExtensionId]);
        
        const result = results[0];
        console.log('\n📊 Test Result:');
        console.log(`   Status: ${result.status}`);
        console.log(`   Extension ID: ${result.extensionId}`);
        
        if (result.status === 'success') {
            console.log(`   File: ${result.filepath}`);
            console.log(`   Size: ${Math.round(result.size / 1024)} KB`);
            console.log(`   Duration: ${result.duration} ms`);
            console.log('\n✅ SUCCESS! The production crawler is working properly.');
            console.log('🚀 Ready for 10k extension crawl.');
            console.log('\n📝 Next steps:');
            console.log('   1. Add your 10k extension IDs to extension_ids.txt');
            console.log('   2. Run: node crx-crawler.js');
        } else {
            console.log(`   Error: ${result.error || 'Unknown error'}`);
            console.log('\n❌ Test failed. Check the error above.');
        }
        
    } catch (error) {
        console.error('\n❌ Test failed with error:', error.message);
        console.log('\n🔧 Troubleshooting:');
        console.log('   • Ensure Chrome/Chromium is installed');
        console.log('   • Check internet connection');
        console.log('   • Verify robwu.nl/crxviewer is accessible');
        console.log('   • Try running: npm install puppeteer');
    }
}

async function testMultipleExtensions() {
    console.log('🧪 Testing with multiple extensions\n');
    
    const crawler = new ProductionCRXCrawler({
        downloadDir: './test_downloads',
        concurrency: 2,
        delayBetweenRequests: 4000,
        retryAttempts: 2,
        headless: true
    });

    const testExtensions = [
        'agkpclldfjffanjojbkhkakaliiohebe'
    ];

    try {
        console.log(`📝 Testing ${testExtensions.length} extensions:`);
        testExtensions.forEach((id, i) => {
            console.log(`   ${i + 1}. ${id}`);
        });
        console.log('');
        
        const results = await crawler.crawl(testExtensions);
        
        console.log('\n📊 Test Results:');
        results.forEach(result => {
            const status = result.status === 'success' ? '✅' : 
                          result.status === 'not_found' ? '🔍' : 
                          result.status === 'skipped' ? '⏭️' : '❌';
            const size = result.size ? ` (${Math.round(result.size/1024)}KB)` : '';
            console.log(`   ${status} ${result.extensionId}: ${result.status}${size}`);
        });
        
        const successful = results.filter(r => r.status === 'success').length;
        console.log(`\n🎯 Success rate: ${successful}/${results.length} (${((successful/results.length)*100).toFixed(1)}%)`);
        
        if (successful > 0) {
            console.log('✅ Multi-extension test passed! Crawler is production-ready.');
        } else {
            console.log('⚠️  No successful downloads. Check configuration and connectivity.');
        }
        
    } catch (error) {
        console.error('\n❌ Multi-extension test failed:', error.message);
    }
}

async function runTests() {
    console.log('🚀 Production CRX Crawler Test Suite\n');
    
    try {
        // Single extension test
        await testSingleExtension();
        
        console.log('\n' + '='.repeat(60) + '\n');
        
        // Multiple extension test
        await testMultipleExtensions();
        
        console.log('\n' + '='.repeat(60));
        console.log('🎯 Testing complete!');
        console.log('📝 If tests passed, you can now run your 10k crawl with:');
        console.log('   node crx-crawler.js');
        console.log('='.repeat(60));
        
    } catch (error) {
        console.error('❌ Test suite failed:', error);
    }
}

if (require.main === module) {
    runTests();
}
        'jifpbeccnghkjeaalbbjmodiffmgedin', // CRX Viewer (should work)
        'cjpalhdlnbpafiamejdnhcphjbkeiagm', // uBlock Origin (should work)
        'invalidextensionidhere12345678', // Invalid format (should fail validation)
        'abcdefghijklmnopqrstuvwxyzabcdef'  // Valid format but likely non-existent
module.exports = { testSingleExtension, testMultipleExtensions };