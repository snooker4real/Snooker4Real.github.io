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

// Filter projects
const filterBtns = document.querySelectorAll('[data-filter-btn]');
const projectItems = document.querySelectorAll('[data-filter-item]');

filterBtns.forEach(btn => {
    btn.addEventListener('click', function() {
        // Remove active class from all buttons
        filterBtns.forEach(b => b.classList.remove('active'));
        // Add active class to clicked button
        this.classList.add('active');

        const filterValue = this.textContent.trim();

        projectItems.forEach(item => {
            const category = item.getAttribute('data-category');

            if (filterValue === 'All' || category === filterValue.toLowerCase()) {
                item.classList.add('active');
                item.style.display = 'block';
            } else {
                item.classList.remove('active');
                item.style.display = 'none';
            }
        });
    });
});

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

// Map of i18n keys to page names
const navMapping = {
    'navAbout': 'about',
    'navResume': 'resume',
    'navPortfolio': 'portfolio',
    'navContact': 'contact',
    'navBlog': 'blog'
};

// add event to all nav link
for (let i = 0; i < navigationLinks.length; i++) {
    navigationLinks[i].addEventListener("click", function () {
        const i18nKey = this.getAttribute('data-i18n');
        const targetPage = navMapping[i18nKey] || this.innerHTML.toLowerCase();

        for (let j = 0; j < pages.length; j++) {
            if (targetPage === pages[j].dataset.page) {
                pages[j].classList.add("active");
                navigationLinks[j].classList.add("active");
                window.scrollTo(0, 0);
            } else {
                pages[j].classList.remove("active");
                navigationLinks[j].classList.remove("active");
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
window.typingText = typingText;
if (typingText) {
    // Get initial texts from translations
    const lang = localStorage.getItem('selected-language') || 'en';
    window.currentTypingRoles = translations && translations[lang] ? translations[lang].heroRoles : [
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
        const texts = window.currentTypingRoles;
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

// Language Toggle functionality
const languageButton = document.getElementById('language-button');
const navbarLanguageButton = document.getElementById('navbar-language-button');
let currentLanguage = localStorage.getItem('selected-language') || 'en';

// Set initial language
document.documentElement.lang = currentLanguage;
updateLanguage(currentLanguage);
updateLanguageButtonDisplay(currentLanguage);

function updateLanguage(lang) {
    if (!translations || !translations[lang]) return;

    const t = translations[lang];

    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (t[key]) {
            element.textContent = t[key];
        }
    });

    // Update typing animation roles
    if (window.typingText) {
        window.currentTypingRoles = t.heroRoles;
    }

    // Update sidebar
    const sidebarBtn = document.querySelector('[data-sidebar-btn] span');
    if (sidebarBtn) {
        const isExpanded = document.querySelector('[data-sidebar]').classList.contains('active');
        sidebarBtn.textContent = isExpanded ? t.hideContacts : t.showContacts;
    }

    // Update contact labels
    updateContactLabels(t);

    // Update page titles and sections
    updatePageContent(t);

    // Update form placeholders
    updateFormPlaceholders(t);

    // Store current language
    localStorage.setItem('selected-language', lang);
    document.documentElement.lang = lang;
}

function updateContactLabels(t) {
    const contactTitles = document.querySelectorAll('.contact-title');
    const labels = ['email', 'phone', 'birthday', 'location'];
    contactTitles.forEach((title, index) => {
        if (labels[index]) {
            title.textContent = t[labels[index]];
        }
    });

    // Update download CV button
    const downloadBtn = document.querySelector('.download-btn span');
    if (downloadBtn) downloadBtn.textContent = t.downloadCV;
}

function updatePageContent(t) {
    // Hero section
    const heroGreeting = document.querySelector('.hero-greeting');
    if (heroGreeting) heroGreeting.textContent = t.heroGreeting;

    const heroDescription = document.querySelector('.hero-description');
    if (heroDescription) heroDescription.textContent = t.heroDescription;

    // CTA buttons
    const ctaBtns = document.querySelectorAll('.cta-btn span');
    if (ctaBtns[0]) ctaBtns[0].textContent = t.viewMyWork;
    if (ctaBtns[1]) ctaBtns[1].textContent = t.getInTouch;

    // Stats labels
    const statLabels = document.querySelectorAll('.stat-label');
    const stats = ['yearsExperience', 'projectsCompleted', 'happyClients', 'technologies'];
    statLabels.forEach((label, index) => {
        if (stats[index]) {
            label.textContent = t[stats[index]];
        }
    });

    // About section
    const aboutTitle = document.querySelector('.about .article-title');
    if (aboutTitle) aboutTitle.textContent = t.aboutTitle;

    const aboutTexts = document.querySelectorAll('.about-text p');
    if (aboutTexts[0]) aboutTexts[0].textContent = t.aboutText1;
    if (aboutTexts[1]) aboutTexts[1].textContent = t.aboutText2;

    // Services section
    const serviceTitle = document.querySelector('.service-title');
    if (serviceTitle) serviceTitle.textContent = t.servicesTitle;

    const serviceTitles = document.querySelectorAll('.service-item-title');
    const serviceTexts = document.querySelectorAll('.service-item-text');
    const services = [
        { title: 'serviceWeb', text: 'serviceWebDesc' },
        { title: 'serviceMobile', text: 'serviceMobileDesc' },
        { title: 'serviceDesign', text: 'serviceDesignDesc' },
        { title: 'serviceWeb3', text: 'serviceWeb3Desc' }
    ];

    services.forEach((service, index) => {
        if (serviceTitles[index]) serviceTitles[index].textContent = t[service.title];
        if (serviceTexts[index]) serviceTexts[index].textContent = t[service.text];
    });

    // Tech stack
    const techStackTitle = document.querySelector('.tech-stack-title');
    if (techStackTitle) techStackTitle.textContent = t.techStackTitle;

    // Testimonials
    const testimonialsTitle = document.querySelector('.testimonials-title');
    if (testimonialsTitle) testimonialsTitle.textContent = t.testimonialsTitle;

    const testimonialTitles = document.querySelectorAll('.testimonials-item-title');
    if (testimonialTitles[0]) testimonialTitles[0].textContent = t.testimonial1Title;
    if (testimonialTitles[1]) testimonialTitles[1].textContent = t.testimonial2Title;

    const testimonialTexts = document.querySelectorAll('.testimonials-text p');
    if (testimonialTexts[0]) testimonialTexts[0].textContent = t.testimonial1Text;
    if (testimonialTexts[1]) testimonialTexts[1].textContent = t.testimonial2Text;

    // Resume section
    const resumeTitle = document.querySelector('.resume .article-title');
    if (resumeTitle) resumeTitle.textContent = t.resumeTitle;

    const educationTitle = document.querySelectorAll('.timeline .h3')[0];
    const experienceTitle = document.querySelectorAll('.timeline .h3')[1];
    if (educationTitle) educationTitle.textContent = t.educationTitle;
    if (experienceTitle) experienceTitle.textContent = t.experienceTitle;

    const skillsTitle = document.querySelector('.skills-title');
    if (skillsTitle) skillsTitle.textContent = t.skillsTitle;

    // Skills categories
    const skillsCategoryTitles = document.querySelectorAll('.skills-category-title');
    const categories = ['skillsFrontend', 'skillsBackend', 'skillsDatabase', 'skillsMobile', 'skillsDevOps', 'skillsWeb3', 'skillsProfessional'];
    skillsCategoryTitles.forEach((title, index) => {
        if (categories[index] && t[categories[index]]) {
            // Keep the icon, only update text
            const textNode = Array.from(title.childNodes).find(node => node.nodeType === Node.TEXT_NODE);
            if (textNode) {
                textNode.textContent = t[categories[index]];
            } else {
                title.append(document.createTextNode(t[categories[index]]));
            }
        }
    });

    // Portfolio section
    const portfolioTitle = document.querySelector('.portfolio .article-title');
    if (portfolioTitle) portfolioTitle.textContent = t.portfolioTitle;

    // Update filter buttons
    const filterButtons = document.querySelectorAll('[data-filter-btn]');
    const filters = ['filterAll', 'filterCrypto', 'filterEcommerce', 'filterTools', 'filterAnime', 'filterVideo', 'filterProductivity'];
    filterButtons.forEach((btn, index) => {
        if (filters[index]) {
            btn.textContent = t[filters[index]];
        }
    });

    // Update select items
    const selectItems = document.querySelectorAll('[data-select-item]');
    selectItems.forEach((item, index) => {
        if (filters[index]) {
            item.textContent = t[filters[index]];
        }
    });

    // Update select value
    const selectValue = document.querySelector('[data-selecct-value]');
    if (selectValue) selectValue.textContent = t.selectCategory;

    // Contact section
    const contactTitle = document.querySelector('.contact .article-title');
    if (contactTitle) contactTitle.textContent = t.contactTitle;

    const formTitle = document.querySelector('.form-title');
    if (formTitle) formTitle.textContent = t.formTitle;

    // Blog section
    const blogTitle = document.querySelector('.blog .article-title');
    if (blogTitle) blogTitle.textContent = t.blogTitle;

    const blogLoading = document.querySelector('#blog-loading p');
    if (blogLoading) blogLoading.textContent = t.blogLoading;

    // Update "Present" text in timeline
    const timelineSpans = document.querySelectorAll('.timeline-item span');
    timelineSpans.forEach(span => {
        if (span.textContent.includes('Present') || span.textContent.includes('Présent')) {
            span.textContent = span.textContent.replace(/Present|Présent/, t.present);
        }
    });
}

function updateFormPlaceholders(t) {
    const fullNameInput = document.querySelector('input[name="fullname"]');
    const emailInput = document.querySelector('input[name="email"]');
    const messageInput = document.querySelector('textarea[name="message"]');
    const sendBtn = document.querySelector('.form-btn span');

    if (fullNameInput) fullNameInput.placeholder = t.fullName;
    if (emailInput) emailInput.placeholder = t.emailAddress;
    if (messageInput) messageInput.placeholder = t.yourMessage;
    if (sendBtn) sendBtn.textContent = t.sendMessage;
}

function updateLanguageButtonDisplay(lang) {
    const currentLangElements = document.querySelectorAll('.current-lang');
    const otherLangElements = document.querySelectorAll('.other-lang');

    currentLangElements.forEach(el => {
        el.textContent = lang.toUpperCase();
    });

    otherLangElements.forEach(el => {
        el.textContent = lang === 'en' ? 'FR' : 'EN';
    });
}

function toggleLanguage() {
    currentLanguage = currentLanguage === 'en' ? 'fr' : 'en';
    updateLanguage(currentLanguage);
    updateLanguageButtonDisplay(currentLanguage);
}

// Add event listeners to both language buttons
if (languageButton) {
    languageButton.addEventListener('click', toggleLanguage);
}

if (navbarLanguageButton) {
    navbarLanguageButton.addEventListener('click', toggleLanguage);
}

// Update sidebar button text when toggled
const sidebarBtnElement = document.querySelector('[data-sidebar-btn]');
if (sidebarBtnElement) {
    sidebarBtnElement.addEventListener('click', function() {
        setTimeout(() => {
            const t = translations[currentLanguage];
            const isExpanded = document.querySelector('[data-sidebar]').classList.contains('active');
            const btnText = this.querySelector('span');
            if (btnText && t) {
                btnText.textContent = isExpanded ? t.hideContacts : t.showContacts;
            }
        }, 10);
    });
}

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