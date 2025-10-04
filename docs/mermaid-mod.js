
function fixMermaidSVGs() {
    document.querySelectorAll('div.mermaid[data-processed="true"]').forEach(div => {
        const svg = div.querySelector('svg');
        if (svg) {
            const vb = svg.getAttribute('viewBox');
            if (vb) {
                const parts = vb.split(' ');
                const w = parseFloat(parts[2]);
                const h = parseFloat(parts[3]);
                
                // Basic mobile responsiveness
                const isMobile = window.innerWidth <= 768;
                if (isMobile) {
                    // On mobile, let the SVG use its natural size but constrain the container
                    svg.style.width = w + 'px';
                    svg.style.minWidth = w + 'px';
                    svg.style.maxWidth = 'none';
                    
                    // Make the container scrollable and limit its width
                    div.style.maxWidth = '100vw';
                    div.style.overflowX = 'auto';
                    div.style.overflowY = 'auto';
                } else {
                    svg.style.width = w + 'px';
                    svg.style.minWidth = w + 'px';
                    svg.style.maxWidth = 'none';
                }
                
                // Scroll horizontally and vertically to center
                // Use setTimeout to ensure layout is updated
                setTimeout(() => {
                    div.scrollLeft = (svg.scrollWidth - div.clientWidth) / 2;
                    div.scrollTop = (svg.scrollHeight - div.clientHeight) / 2;
                }, 50);
            }
        }
    });
}


function observeMermaidProcessing() {
    // Initial check in case already processed
    fixMermaidSVGs();
    // Observe for new mermaid charts being processed or added
    const observer = new MutationObserver((mutationsList) => {
        // Always observe new div.mermaid for attribute changes
        for (const mutation of mutationsList) {
            mutation.addedNodes && mutation.addedNodes.forEach(node => {
                if (node.nodeType === 1 && node.matches && node.matches('div.mermaid')) {
                    observer.observe(node, { attributes: true });
                }
            });
        }
        // Always run the fix after any mutation
        fixMermaidSVGs();
    });
    // Observe all current and future div.mermaid
    document.querySelectorAll('div.mermaid').forEach(div => {
        observer.observe(div, { attributes: true });
    });
    // Also observe the document for new div.mermaid elements
    observer.observe(document.body, { childList: true, subtree: true });
}
document.addEventListener("DOMContentLoaded", observeMermaidProcessing);

// Re-apply fixes on window resize for orientation changes
window.addEventListener('resize', () => {
    setTimeout(fixMermaidSVGs, 100);
});

// Random Page Generator - Fully Dynamic Discovery
async function discoverPages() {
    const pages = [];
    
    try {
        // Method 1: Try sitemap.xml (most reliable for MkDocs)
        const sitemapResponse = await fetch('/sitemap.xml');
        if (sitemapResponse.ok) {
            const text = await sitemapResponse.text();
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(text, "text/xml");
            const urls = xmlDoc.querySelectorAll('url loc');
            
            urls.forEach(url => {
                const href = url.textContent;
                // Match any /category/page/ pattern (no /en prefix), extract category/page
                const match = href.match(/\/([^\/]+)\/([^\/]+)\/$/);
                if (match && match[1] !== 'about' && match[1] !== 'search') { // exclude about and search pages
                    pages.push(`${match[1]}/${match[2]}`);
                }
            });
            
            if (pages.length > 0) {
                console.log(`Found ${pages.length} pages from sitemap`);
                return pages;
            }
        }
        
        // Method 2: Try search index
        const searchResponse = await fetch('/search/search_index.json');
        if (searchResponse.ok) {
            const searchData = await searchResponse.json();
            if (searchData.docs) {
                searchData.docs.forEach(doc => {
                    const match = doc.location.match(/([^\/]+)\/([^\/]+)\/$/);
                    if (match && match[1] !== 'about' && match[1] !== 'search') {
                        pages.push(`${match[1]}/${match[2]}`);
                    }
                });
            }
            
            if (pages.length > 0) {
                console.log(`Found ${pages.length} pages from search index`);
                return pages;
            }
        }
        
        // Method 3: Crawl navigation (fallback)
        const navLinks = document.querySelectorAll('nav a[href]');
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            const match = href.match(/\/([^\/]+)\/([^\/]+)\/$/);
            if (match && match[1] !== 'about' && match[1] !== 'search') {
                pages.push(`${match[1]}/${match[2]}`);
            }
        });
        
        console.log(`Found ${pages.length} pages from navigation crawl`);
        return pages;
        
    } catch (error) {
        console.error('Error discovering pages:', error);
        return [];
    }
}

function resetRandomButton() {
    const button = document.getElementById('random-page') || document.querySelector('.random-page');
    if (button) {
        button.textContent = '🎲 Go to Random Page';
        button.disabled = false;
    }
}

async function goToRandomPage() {
    const button = document.getElementById('random-page') || document.querySelector('.random-page');
    
    // Show loading state
    if (button) {
        button.textContent = '🔄 Finding page...';
        button.disabled = true;
    }
    
    try {
        const pages = await discoverPages();
        
        if (pages.length === 0) {
            console.error('No pages found for random selection');
            if (button) {
                button.textContent = '❌ No pages found';
                setTimeout(resetRandomButton, 2000);
            }
            return;
        }
        
        const randomIndex = Math.floor(Math.random() * pages.length);
        const randomPage = pages[randomIndex];
        
        console.log(`Navigating to random page: ${randomPage} (${randomIndex + 1}/${pages.length})`);
        
        // Navigate to the random page
        window.location.href = `/${randomPage}/`;
        
    } catch (error) {
        console.error('Error selecting random page:', error);
        if (button) {
            button.textContent = '❌ Error occurred';
            setTimeout(resetRandomButton, 2000);
        }
    }
}

// Add random page button functionality
document.addEventListener("DOMContentLoaded", () => {
    // Reset button state on page load (handles back button case)
    resetRandomButton();
    
    const randomButtons = document.querySelectorAll('.random-page, #random-page');
    randomButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            await goToRandomPage();
        });
    });
});

// Also handle page show event (fires on back/forward navigation)
window.addEventListener('pageshow', () => {
    resetRandomButton();
});

// Handle visibility change (when tab becomes visible again)
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        resetRandomButton();
    }
});