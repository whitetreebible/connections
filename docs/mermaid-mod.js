
function fixMermaidSVGs() {
    document.querySelectorAll('div.mermaid[data-processed="true"]').forEach(div => {
        const svg = div.querySelector('svg');
        if (svg) {
            const vb = svg.getAttribute('viewBox');
            if (vb) {
                const parts = vb.split(' ');
                const w = parseFloat(parts[2]);
                const h = parseFloat(parts[3]);
                svg.style.width = w + 'px';
                svg.style.minWidth = w + 'px';
                svg.style.maxWidth = 'none';
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