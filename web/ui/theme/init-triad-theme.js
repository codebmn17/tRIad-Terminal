/**
 * Triad Terminal Theme Initializer
 *
 * Automatically applies the Triad theme and ensures proper header setup
 * when the DOM is loaded. This script is safe to include multiple times.
 */

(function() {
  'use strict';

  /**
   * Initialize the Triad theme
   */
  function initTriadTheme() {
    // Add the theme class to body
    document.body.classList.add('triad-theme');

    // Find and enhance any existing headers
    const headers = document.querySelectorAll('.triad-header');
    headers.forEach(enhanceHeader);

    console.log('Triad theme initialized');
  }

  /**
   * Enhance a header element with proper triangle icon
   * @param {Element} header - The header element to enhance
   */
  function enhanceHeader(header) {
    // Check if header already has triangle icon
    if (header.querySelector('.triangle-icon')) {
      return; // Already enhanced
    }

    // Ensure header has proper structure
    ensureHeaderStructure(header);

    // Add triangle icon to the right side
    const headerRight = header.querySelector('.header-right');
    if (headerRight) {
      const triangleIcon = createTriangleIcon();
      headerRight.appendChild(triangleIcon);
    }
  }

  /**
   * Ensure header has the proper three-section structure
   * @param {Element} header - The header element to structure
   */
  function ensureHeaderStructure(header) {
    let headerLeft = header.querySelector('.header-left');
    let headerCenter = header.querySelector('.header-center');
    let headerRight = header.querySelector('.header-right');

    // Create missing sections
    if (!headerLeft) {
      headerLeft = document.createElement('div');
      headerLeft.className = 'header-left';
      header.appendChild(headerLeft);
    }

    if (!headerCenter) {
      headerCenter = document.createElement('div');
      headerCenter.className = 'header-center';

      // If there's existing content, move it to center
      const existingTitle = header.querySelector('.title') || header.querySelector('h1');
      if (existingTitle) {
        headerCenter.appendChild(existingTitle);
      } else {
        // Create default title
        const title = document.createElement('h1');
        title.className = 'title';
        title.textContent = 'TRIAD TERMINAL';
        headerCenter.appendChild(title);
      }

      header.appendChild(headerCenter);
    }

    if (!headerRight) {
      headerRight = document.createElement('div');
      headerRight.className = 'header-right';
      header.appendChild(headerRight);
    }

    // Add mask icon to left side if not present
    if (!headerLeft.querySelector('.mask-icon')) {
      const maskIcon = createMaskIcon();
      if (maskIcon) {
        headerLeft.appendChild(maskIcon);
      }
    }
  }

  /**
   * Create the triangle icon element
   * @returns {Element} The triangle icon img element
   */
  function createTriangleIcon() {
    const img = document.createElement('img');
    img.src = '/assets/images/triad-triangle.svg';
    img.alt = 'Triad Triangle';
    img.className = 'triangle-icon';

    // Handle missing image gracefully
    img.onerror = function() {
      console.warn('Triangle icon not found at /assets/images/triad-triangle.svg');
      // Keep the element but make it invisible rather than showing broken image
      this.style.opacity = '0.3';
      this.alt = 'Triangle (missing)';
    };

    return img;
  }

  /**
   * Create the mask icon element if the image exists
   * @returns {Element|null} The mask icon img element or null if not available
   */
  function createMaskIcon() {
    const img = document.createElement('img');
    img.src = '/assets/images/anon-mask.svg';
    img.alt = 'Anonymous Mask';
    img.className = 'mask-icon';

    // Handle missing image by removing the element
    img.onerror = function() {
      console.info('Mask icon not found at /assets/images/anon-mask.svg - skipping');
      if (this.parentNode) {
        this.parentNode.removeChild(this);
      }
    };

    return img;
  }

  /**
   * Create a complete header if none exists
   */
  function createDefaultHeader() {
    const header = document.createElement('header');
    header.className = 'triad-header';

    // Left section with mask
    const headerLeft = document.createElement('div');
    headerLeft.className = 'header-left';
    const maskIcon = createMaskIcon();
    if (maskIcon) {
      headerLeft.appendChild(maskIcon);
    }

    // Center section with title
    const headerCenter = document.createElement('div');
    headerCenter.className = 'header-center';
    const title = document.createElement('h1');
    title.className = 'title';
    title.textContent = 'TRIAD TERMINAL';
    headerCenter.appendChild(title);

    // Right section with triangle
    const headerRight = document.createElement('div');
    headerRight.className = 'header-right';
    const triangleIcon = createTriangleIcon();
    headerRight.appendChild(triangleIcon);

    // Assemble header
    header.appendChild(headerLeft);
    header.appendChild(headerCenter);
    header.appendChild(headerRight);

    // Insert at top of body
    document.body.insertBefore(header, document.body.firstChild);

    return header;
  }

  /**
   * Auto-create header if requested via data attribute
   */
  function autoCreateHeader() {
    if (document.body.dataset.triadAutoHeader === 'true') {
      if (!document.querySelector('.triad-header')) {
        createDefaultHeader();
        console.log('Auto-created Triad header');
      }
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initTriadTheme();
      autoCreateHeader();
    });
  } else {
    // DOM already ready
    initTriadTheme();
    autoCreateHeader();
  }

  // Expose functions globally for manual use
  window.TriadTheme = {
    init: initTriadTheme,
    enhanceHeader: enhanceHeader,
    createDefaultHeader: createDefaultHeader
  };

})();
