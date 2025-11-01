'use strict';

// element toggle function
const elementToggleFunc = function (elem) { elem.classList.toggle("active"); }

// sidebar variables
const sidebar = document.querySelector("[data-sidebar]");
const sidebarBtn = document.querySelector("[data-sidebar-btn]");

// sidebar toggle functionality for mobile
sidebarBtn.addEventListener("click", function () { elementToggleFunc(sidebar); });

// testimonials variables
const testimonialsItem = document.querySelectorAll("[data-testimonials-item]");
const modalContainer = document.querySelector("[data-modal-container]");
const modalCloseBtn = document.querySelector("[data-modal-close-btn]");
const overlay = document.querySelector("[data-overlay]");

// modal variable
const modalImg = document.querySelector("[data-modal-img]");
const modalTitle = document.querySelector("[data-modal-title]");
const modalText = document.querySelector("[data-modal-text]");

// modal toggle function
const testimonialsModalFunc = function () {
    modalContainer.classList.toggle("active");
    overlay.classList.toggle("active");
}

// add click event to all modal items
for (let i = 0; i < testimonialsItem.length; i++) {
    testimonialsItem[i].addEventListener("click", function () {
        modalImg.src = this.querySelector("[data-testimonials-avatar]").src;
        modalImg.alt = this.querySelector("[data-testimonials-avatar]").alt;
        modalTitle.innerHTML = this.querySelector("[data-testimonials-title]").innerHTML;
        modalText.innerHTML = this.querySelector("[data-testimonials-text]").innerHTML;
        testimonialsModalFunc();
    });
}

// add click event to modal close button
modalCloseBtn.addEventListener("click", testimonialsModalFunc);
overlay.addEventListener("click", testimonialsModalFunc);

// custom select variables
const select = document.querySelector("[data-select]");
const selectItems = document.querySelectorAll("[data-select-item]");
const selectValue = document.querySelector("[data-selecct-value]");
const filterBtn = document.querySelectorAll("[data-filter-btn]");

select.addEventListener("click", function () { elementToggleFunc(this); });

// add event in all select items
for (let i = 0; i < selectItems.length; i++) {
    selectItems[i].addEventListener("click", function () {
        let selectedValue = this.innerText.toLowerCase();
        selectValue.innerText = this.innerText;
        elementToggleFunc(select);
        filterFunc(selectedValue);
    });
}

// filter variables
const filterItems = document.querySelectorAll("[data-filter-item]");


// add event in all filter button items for large screen
let lastClickedBtn = filterBtn[0];

for (let i = 0; i < filterBtn.length; i++) {
    filterBtn[i].addEventListener("click", function () {
        let selectedValue = this.innerText.toLowerCase();
        selectValue.innerText = this.innerText;
        filterFunc(selectedValue);
        lastClickedBtn.classList.remove("active");
        this.classList.add("active");
        lastClickedBtn = this;
    });
}

// contact form variables
const form = document.querySelector("[data-form]");
const formInputs = document.querySelectorAll("[data-form-input]");
const formBtn = document.querySelector("[data-form-btn]");

// add event to all form input field
for (let i = 0; i < formInputs.length; i++) {
    formInputs[i].addEventListener("input", function () {
        // check form validation
        if (form.checkValidity()) {
            formBtn.removeAttribute("disabled");
        } else {
            formBtn.setAttribute("disabled", "");
        }
    });
}

// page navigation variables
const navigationLinks = document.querySelectorAll("[data-nav-link]");
const pages = document.querySelectorAll("[data-page]");

// add event to all nav link
for (let i = 0; i < navigationLinks.length; i++) {
    navigationLinks[i].addEventListener("click", function () {
        for (let i = 0; i < pages.length; i++) {
            if (this.innerHTML.toLowerCase() === pages[i].dataset.page) {
                pages[i].classList.add("active");
                navigationLinks[i].classList.add("active");
                window.scrollTo(0, 0);
            } else {
                pages[i].classList.remove("active");
                navigationLinks[i].classList.remove("active");
            }
        }
    });
}

// Theme toggle functionality (keeping your original theme logic)
const themeButton = document.getElementById('theme-button');
const darkTheme = 'dark-theme';
const iconTheme = 'uil-sun';

// Check if user previously selected a theme
const selectedTheme = localStorage.getItem('selected-theme');
const selectedIcon = localStorage.getItem('selected-icon');

const getCurrentTheme = () => document.body.classList.contains(darkTheme) ? 'dark' : 'light';
const getCurrentIcon = () => themeButton.classList.contains(iconTheme) ? 'uil-moon' : 'uil-sun';

if (selectedTheme) {
    document.body.classList[selectedTheme === 'dark' ? 'add' : 'remove'](darkTheme);
    if (themeButton) {
        themeButton.classList[selectedIcon === 'uil-moon' ? 'add' : 'remove'](iconTheme);
    }
}

if (themeButton) {
    themeButton.addEventListener('click', () => {
        document.body.classList.toggle(darkTheme);
        themeButton.classList.toggle(iconTheme);
        localStorage.setItem('selected-theme', getCurrentTheme());
        localStorage.setItem('selected-icon', getCurrentIcon());
    });
}

// Initialize form button state
if (form && formBtn) {
    if (form.checkValidity()) {
        formBtn.removeAttribute("disabled");
    } else {
        formBtn.setAttribute("disabled", "");
    }
}

// Update the filter function to handle all categories
const filterFunc = function (selectedValue) {
    for (let i = 0; i < filterItems.length; i++) {
        if (selectedValue === "all") {
            filterItems[i].classList.add("active");
        } else if (selectedValue === filterItems[i].dataset.category) {
            filterItems[i].classList.add("active");
        } else {
            filterItems[i].classList.remove("active");
        }
    }
}

// Initialize all projects as active
document.addEventListener('DOMContentLoaded', function() {
    const projects = document.querySelectorAll('.project-item');
    projects.forEach(project => {
        project.classList.add('active');
    });
});

// Skills animation on scroll
function animateSkillsOnScroll() {
    const skillsSection = document.querySelector('.skill');
    const skillItems = document.querySelectorAll('.skills-item');

    if (!skillsSection) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                skillItems.forEach((item, index) => {
                    setTimeout(() => {
                        item.style.animation = `fadeInUp 0.6s ease forwards`;
                    }, index * 100);
                });
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.3 });

    observer.observe(skillsSection);
}

// Initialize skills animation
document.addEventListener('DOMContentLoaded', function() {
    animateSkillsOnScroll();

    // Animate progress bars when they come into view
    const progressBars = document.querySelectorAll('.skill-progress-fill');

    const progressObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const width = entry.target.style.width;
                entry.target.style.width = '0%';
                setTimeout(() => {
                    entry.target.style.width = width;
                }, 100);
                progressObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    progressBars.forEach(bar => {
        progressObserver.observe(bar);
    });
});

// Blog - Fetch Substack articles
async function fetchSubstackArticles() {
    const blogPostsList = document.getElementById('blog-posts-list');
    const blogLoading = document.getElementById('blog-loading');
    const blogError = document.getElementById('blog-error');

    try {
        // Use RSS2JSON API to convert RSS feed to JSON (handles CORS)
        const rssUrl = 'https://cindanojonathan.substack.com/feed';
        const apiUrl = `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(rssUrl)}&count=10`;

        const response = await fetch(apiUrl);
        const data = await response.json();

        if (data.status !== 'ok') {
            throw new Error('Failed to fetch articles');
        }

        // Hide loading, show posts
        blogLoading.style.display = 'none';

        // Clear existing content
        blogPostsList.innerHTML = '';

        // If no articles found
        if (!data.items || data.items.length === 0) {
            blogError.style.display = 'flex';
            return;
        }

        // Create article cards
        data.items.forEach(article => {
            const articleItem = createBlogPostCard(article);
            blogPostsList.appendChild(articleItem);
        });

    } catch (error) {
        console.error('Error fetching Substack articles:', error);
        blogLoading.style.display = 'none';
        blogError.style.display = 'flex';
    }
}

function createBlogPostCard(article) {
    const li = document.createElement('li');
    li.className = 'blog-post-item';

    // Extract image from content or use thumbnail
    let imageUrl = article.thumbnail || article.enclosure?.link || '';

    // If no image, try to extract from content
    if (!imageUrl && article.content) {
        const imgMatch = article.content.match(/<img[^>]+src="([^">]+)"/);
        if (imgMatch) {
            imageUrl = imgMatch[1];
        }
    }

    // Format date
    const publishDate = new Date(article.pubDate);
    const formattedDate = publishDate.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });

    // Extract excerpt (remove HTML tags)
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = article.description || article.content || '';
    const excerpt = tempDiv.textContent.trim().substring(0, 150) + '...';

    li.innerHTML = `
        <a href="${article.link}" target="_blank" rel="noopener noreferrer" class="blog-post-link">
            ${imageUrl ? `
            <figure class="blog-post-banner">
                <img src="${imageUrl}" alt="${article.title}" loading="lazy">
            </figure>
            ` : ''}
            <div class="blog-post-content">
                <div class="blog-post-meta">
                    <div class="blog-post-date">
                        <ion-icon name="calendar-outline"></ion-icon>
                        <time datetime="${article.pubDate}">${formattedDate}</time>
                    </div>
                </div>
                <h3 class="blog-post-title">${article.title}</h3>
                <p class="blog-post-excerpt">${excerpt}</p>
                <div class="blog-read-more">
                    <span>Read article</span>
                    <ion-icon name="arrow-forward-outline"></ion-icon>
                </div>
            </div>
        </a>
    `;

    return li;
}

// Load blog articles when blog page becomes active
const blogPage = document.querySelector('[data-page="blog"]');
let blogLoaded = false;

// Observer to detect when blog page is shown
const blogObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.target.classList.contains('active') && !blogLoaded) {
            blogLoaded = true;
            fetchSubstackArticles();
        }
    });
});

if (blogPage) {
    blogObserver.observe(blogPage, { attributes: true, attributeFilter: ['class'] });

    // If blog is already active on page load, fetch immediately
    if (blogPage.classList.contains('active')) {
        blogLoaded = true;
        fetchSubstackArticles();
    }
}

// Hero - Typing Animation
const typingText = document.getElementById('typing-text');
if (typingText) {
    const texts = [
        'Full Stack Developer',
        'Web3 Enthusiast',
        'UI/UX Designer',
        'Problem Solver',
        'Mobile App Developer'
    ];
    let textIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let typingSpeed = 100;

    function type() {
        const currentText = texts[textIndex];

        if (isDeleting) {
            typingText.textContent = currentText.substring(0, charIndex - 1);
            charIndex--;
            typingSpeed = 50;
        } else {
            typingText.textContent = currentText.substring(0, charIndex + 1);
            charIndex++;
            typingSpeed = 100;
        }

        if (!isDeleting && charIndex === currentText.length) {
            // Pause at end
            typingSpeed = 2000;
            isDeleting = true;
        } else if (isDeleting && charIndex === 0) {
            isDeleting = false;
            textIndex = (textIndex + 1) % texts.length;
            typingSpeed = 500;
        }

        setTimeout(type, typingSpeed);
    }

    // Start typing animation
    type();
}

// Hero - Animated Counter for Statistics
function animateCounter(element) {
    const target = parseInt(element.getAttribute('data-target'));
    const duration = 2000; // 2 seconds
    const increment = target / (duration / 16); // 60fps
    let current = 0;

    const updateCounter = () => {
        current += increment;
        if (current < target) {
            element.textContent = Math.floor(current);
            requestAnimationFrame(updateCounter);
        } else {
            element.textContent = target;
        }
    };

    updateCounter();
}

// Observe when hero stats come into view
const heroStats = document.querySelector('.hero-stats');
if (heroStats) {
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const statNumbers = entry.target.querySelectorAll('.stat-number');
                statNumbers.forEach(stat => {
                    animateCounter(stat);
                });
                statsObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    statsObserver.observe(heroStats);
}

// Hero CTA - Navigation
const ctaButtons = document.querySelectorAll('[data-nav-to]');
ctaButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        const targetPage = btn.getAttribute('data-nav-to');

        // Find the corresponding nav link and trigger click
        const navLinks = document.querySelectorAll('[data-nav-link]');
        navLinks.forEach(link => {
            if (link.textContent.toLowerCase() === targetPage) {
                link.click();
            }
        });
    });
});

// Case Study Modals
const caseStudyBtns = document.querySelectorAll('[data-project]');
const caseStudyModals = document.querySelectorAll('[data-case-study-modal]');
const caseStudyOverlays = document.querySelectorAll('[data-case-study-overlay]');
const caseStudyCloseBtns = document.querySelectorAll('[data-case-study-close]');

// Function to open case study modal
const openCaseStudyModal = (projectName) => {
    const modal = document.querySelector(`#${projectName}-modal`);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
};

// Function to close case study modal
const closeCaseStudyModal = () => {
    caseStudyModals.forEach(modal => {
        modal.classList.remove('active');
    });
    document.body.style.overflow = 'auto';
};

// Add click event to case study buttons
caseStudyBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const projectName = btn.getAttribute('data-project');
        openCaseStudyModal(projectName);
    });
});

// Add click event to close buttons
caseStudyCloseBtns.forEach(btn => {
    btn.addEventListener('click', closeCaseStudyModal);
});

// Add click event to overlays
caseStudyOverlays.forEach(overlay => {
    overlay.addEventListener('click', closeCaseStudyModal);
});

// Close modal with ESC key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeCaseStudyModal();
    }
});

// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then((registration) => {
                console.log('Service Worker registered successfully:', registration.scope);
            })
            .catch((error) => {
                console.log('Service Worker registration failed:', error);
            });
    });
}