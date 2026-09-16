'use strict';

/* ============================================================
   Jonathan Cindano — Portfolio · interactions
   ============================================================ */

const $  = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ---------- Header shadow + scroll progress + back-to-top ---------- */
const header = $('[data-header]');
const toTop = $('.to-top');
const progress = $('[data-progress]');

const onScroll = () => {
    const y = window.scrollY;
    if (header) header.classList.toggle('is-scrolled', y > 8);
    if (toTop) toTop.classList.toggle('is-visible', y > 600);
    if (progress) {
        const max = document.documentElement.scrollHeight - window.innerHeight;
        progress.style.width = (max > 0 ? (y / max) * 100 : 0) + '%';
    }
};
window.addEventListener('scroll', onScroll, { passive: true });
window.addEventListener('resize', onScroll, { passive: true });
onScroll();

/* ---------- Tech marquee (seamless loop, paused off-screen) ---------- */
const marquee = $('[data-marquee]');
if (marquee) {
    $$('.marquee__row', marquee).forEach(row => { row.innerHTML += row.innerHTML; });
    if ('IntersectionObserver' in window) {
        new IntersectionObserver(([entry]) => {
            marquee.classList.toggle('is-paused', !entry.isIntersecting);
        }, { rootMargin: '120px' }).observe(marquee);
    }
    document.addEventListener('visibilitychange', () => {
        marquee.classList.toggle('is-paused', document.hidden);
    });
}

/* ---------- Mobile navigation ---------- */
const navToggle = $('#nav-toggle');
const siteNav = $('#site-nav');

const closeNav = () => {
    if (!siteNav) return;
    siteNav.classList.remove('is-open');
    navToggle?.setAttribute('aria-expanded', 'false');
    navToggle?.setAttribute('aria-label', 'Open menu');
};

if (navToggle && siteNav) {
    navToggle.addEventListener('click', () => {
        const open = siteNav.classList.toggle('is-open');
        navToggle.setAttribute('aria-expanded', String(open));
        navToggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
    siteNav.addEventListener('click', (e) => {
        if (e.target.closest('a')) closeNav();
    });
    window.addEventListener('resize', () => {
        if (window.innerWidth > 1024) closeNav();
    });
}

/* ---------- Scroll spy ---------- */
const navLinks = $$('[data-nav-link]');
const sections = navLinks
    .map(link => document.getElementById(link.getAttribute('href').slice(1)))
    .filter(Boolean);

if (sections.length) {
    const spy = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const id = entry.target.id;
            navLinks.forEach(link => {
                link.classList.toggle('is-active', link.getAttribute('href') === `#${id}`);
            });
        });
    }, { rootMargin: '-45% 0px -50% 0px', threshold: 0 });
    sections.forEach(sec => spy.observe(sec));
}

/* ---------- Theme ---------- */
const themeButton = $('#theme-button');
const storedTheme = localStorage.getItem('selected-theme');

const applyTheme = (theme) => {
    document.documentElement.classList.toggle('light', theme === 'light');
    localStorage.setItem('selected-theme', theme);
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', theme === 'light' ? '#f3f7f4' : '#0a0f0d');
};

applyTheme(storedTheme === 'light' ? 'light' : 'dark');

themeButton?.addEventListener('click', () => {
    const next = document.documentElement.classList.contains('light') ? 'dark' : 'light';
    applyTheme(next);
});

/* ---------- Internationalisation ---------- */
const languageButtons = ['#language-button'].map(s => $(s)).filter(Boolean);
let currentLanguage = localStorage.getItem('selected-language') || 'en';

function applyTranslations(lang) {
    const t = (typeof translations !== 'undefined' && translations[lang]) ? translations[lang] : null;
    if (!t) return;

    $$('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key] != null) el.textContent = t[key];
    });
    $$('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (t[key] != null) el.setAttribute('placeholder', t[key]);
    });
    $$('[data-i18n-aria]').forEach(el => {
        const key = el.getAttribute('data-i18n-aria');
        if (t[key] != null) el.setAttribute('aria-label', t[key]);
    });
    $$('[data-i18n-html]').forEach(el => {
        const key = el.getAttribute('data-i18n-html');
        if (t[key] != null) el.innerHTML = t[key];
    });

    if (Array.isArray(t.heroRoles)) window.currentTypingRoles = t.heroRoles;

    languageButtons.forEach(btn => {
        const span = btn.querySelector('.current-lang');
        if (span) span.textContent = lang.toUpperCase();
    });

    document.documentElement.lang = lang;
    localStorage.setItem('selected-language', lang);
    window.__lang = lang;
}

function toggleLanguage() {
    currentLanguage = currentLanguage === 'en' ? 'fr' : 'en';
    applyTranslations(currentLanguage);
}

languageButtons.forEach(btn => btn.addEventListener('click', toggleLanguage));
applyTranslations(currentLanguage);

/* ---------- Hero typing animation ---------- */
const typingText = $('#typing-text');
if (typingText) {
    const fallback = ['Full Stack Developer', 'Web3 Enthusiast', 'UI/UX Designer', 'Problem Solver', 'Mobile App Developer'];
    if (!Array.isArray(window.currentTypingRoles)) window.currentTypingRoles = fallback;

    if (prefersReducedMotion) {
        typingText.textContent = window.currentTypingRoles[0];
    } else {
        let roleIndex = 0, charIndex = 0, deleting = false;

        const tick = () => {
            const roles = window.currentTypingRoles;
            const role = roles[roleIndex % roles.length];
            charIndex += deleting ? -1 : 1;
            typingText.textContent = role.slice(0, charIndex);

            let delay = deleting ? 45 : 95;
            if (!deleting && charIndex === role.length) { delay = 1900; deleting = true; }
            else if (deleting && charIndex === 0) { deleting = false; roleIndex++; delay = 420; }
            setTimeout(tick, delay);
        };
        tick();
    }
}

/* ---------- Animated counters ---------- */
const hero = $('.hero');
if (hero) {
    const renderStat = (el, value, suffix) =>
        el.innerHTML = value + (suffix ? `<b>${suffix}</b>` : '');

    const runCounters = () => {
        $$('.stat__value', hero).forEach(el => {
            const target = parseInt(el.getAttribute('data-target'), 10) || 0;
            const suffix = el.getAttribute('data-suffix') || '';
            if (prefersReducedMotion) { renderStat(el, target, suffix); return; }
            const duration = 900;
            const start = performance.now();
            const step = (now) => {
                const p = Math.min((now - start) / duration, 1);
                const eased = 1 - Math.pow(1 - p, 4);
                renderStat(el, Math.round(target * eased), p > 0.9 ? suffix : '');
                if (p < 1) requestAnimationFrame(step);
            };
            requestAnimationFrame(step);
        });
    };
    const statObs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) { runCounters(); statObs.disconnect(); }
        });
    }, { threshold: 0.4 });
    statObs.observe(hero);
}

/* ---------- Skill bars ---------- */
const skillBars = $$('.skill-bar__fill');
if (skillBars.length) {
    skillBars.forEach(bar => {
        bar.dataset.target = bar.style.width || '0%';
        if (!prefersReducedMotion) bar.style.width = '0%';
    });
    const barObs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const bar = entry.target;
            requestAnimationFrame(() => { bar.style.width = bar.dataset.target; });
            barObs.unobserve(bar);
        });
    }, { threshold: 0.5 });
    skillBars.forEach(bar => barObs.observe(bar));
}

/* ---------- CV dropdown ---------- */
const cv = $('[data-cv]');
const cvToggle = $('[data-cv-toggle]');
if (cv && cvToggle) {
    cvToggle.addEventListener('click', () => {
        const open = cv.classList.toggle('is-open');
        cvToggle.setAttribute('aria-expanded', String(open));
    });
    document.addEventListener('click', (e) => {
        if (!cv.contains(e.target) && cv.classList.contains('is-open')) {
            cv.classList.remove('is-open');
            cvToggle.setAttribute('aria-expanded', 'false');
        }
    });
}

/* ---------- Portfolio filter ---------- */
const filterButtons = $$('.filter');
const filterItems = $$('[data-filter-item]');
filterButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        filterButtons.forEach(b => b.classList.remove('is-active'));
        btn.classList.add('is-active');
        const value = btn.dataset.filter;
        filterItems.forEach(item => {
            const show = value === 'all' || item.dataset.category === value;
            item.hidden = !show;
        });
    });
});

/* ---------- Testimonials modal ---------- */
const tModal = $('[data-modal-container]');
if (tModal) {
    const tImg = $('[data-modal-img]', tModal);
    const tTitle = $('[data-modal-title]', tModal);
    const tText = $('[data-modal-text]', tModal);
    const toggleTModal = () => tModal.classList.toggle('active');

    $$('[data-testimonials-item]').forEach(item => {
        item.addEventListener('click', () => {
            const avatar = $('[data-testimonials-avatar]', item);
            if (avatar && tImg) { tImg.src = avatar.src; tImg.alt = avatar.alt; }
            if (tTitle) tTitle.textContent = $('[data-testimonials-title]', item)?.textContent.trim() || '';
            if (tText) tText.innerHTML = $('[data-testimonials-text]', item)?.innerHTML || '';
            tModal.classList.add('active');
        });
    });
    $('[data-modal-close-btn]', tModal)?.addEventListener('click', toggleTModal);
    $('[data-overlay]', tModal)?.addEventListener('click', toggleTModal);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') tModal.classList.remove('active');
    });
}

/* ---------- Case study modals ---------- */
const caseModals = $$('[data-case-study-modal]');
const closeCaseModals = () => {
    caseModals.forEach(m => m.classList.remove('active'));
    document.body.style.overflow = '';
};
$$('[data-project]').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const modal = document.getElementById(`${btn.dataset.project}-modal`);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    });
});
$$('[data-case-study-close]').forEach(btn => btn.addEventListener('click', closeCaseModals));
$$('[data-case-study-overlay]').forEach(ov => ov.addEventListener('click', closeCaseModals));
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeCaseModals();
});

/* ---------- Contact form validation ---------- */
const form = $('[data-form]');
const formBtn = $('[data-form-btn]');
if (form && formBtn) {
    const sync = () => formBtn.toggleAttribute('disabled', !form.checkValidity());
    form.addEventListener('input', sync);
    sync();
}

/* ---------- Reveal on scroll ---------- */
if (!prefersReducedMotion && 'IntersectionObserver' in window) {
    const revealObs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-in');
                revealObs.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    $$('.section-head, .section-lead, .about-panel, .marquee, .testimonials, .resume-grid, .skills-grid, .filters, .contact-grid, .blog-grid')
        .forEach(el => { el.classList.add('reveal'); revealObs.observe(el); });

    $$('.project').forEach((el, i) => {
        el.classList.add('reveal');
        el.style.transitionDelay = `${Math.min(i, 5) * 45}ms`;
        revealObs.observe(el);
    });
}

/* ---------- Blog (Substack via rss2json) ---------- */
const blogSection = $('#blog');
let blogLoaded = false;

function blogDate(dateStr) {
    const d = new Date(dateStr);
    const locale = (window.__lang === 'fr') ? 'fr-FR' : 'en-US';
    return d.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' });
}

function createBlogPostCard(article) {
    const li = document.createElement('li');
    li.className = 'blog-post-item';

    let imageUrl = article.thumbnail || article.enclosure?.link || '';
    if (!imageUrl && article.content) {
        const m = article.content.match(/<img[^>]+src="([^">]+)"/);
        if (m) imageUrl = m[1];
    }

    const tmp = document.createElement('div');
    tmp.innerHTML = article.description || article.content || '';
    const excerpt = tmp.textContent.trim().slice(0, 150).trim() + '…';

    const readLabel = (typeof translations !== 'undefined' && translations[window.__lang || 'en']?.readArticle) || 'Read article';

    li.innerHTML = `
        <a href="${article.link}" target="_blank" rel="noopener noreferrer" class="blog-post-link">
            ${imageUrl ? `<figure class="blog-post-banner"><img src="${imageUrl}" alt="" loading="lazy"></figure>` : ''}
            <div class="blog-post-content">
                <div class="blog-post-meta">
                    <span class="blog-post-date">
                        <ion-icon name="calendar-outline"></ion-icon>
                        <time datetime="${article.pubDate}">${blogDate(article.pubDate)}</time>
                    </span>
                </div>
                <h3 class="blog-post-title">${article.title}</h3>
                <p class="blog-post-excerpt">${excerpt}</p>
                <span class="blog-read-more">${readLabel} <ion-icon name="arrow-forward-outline"></ion-icon></span>
            </div>
        </a>`;
    return li;
}

async function fetchSubstackArticles() {
    const list = $('#blog-posts-list');
    const loading = $('#blog-loading');
    const error = $('#blog-error');
    try {
        const rssUrl = 'https://cindanojonathan.substack.com/feed';
        const apiUrl = `https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(rssUrl)}`;
        const res = await fetch(apiUrl);
        const data = await res.json();
        if (data.status !== 'ok' || !Array.isArray(data.items)) throw new Error('feed error');

        loading?.setAttribute('hidden', '');
        list.innerHTML = '';
        if (!data.items.length) { error?.removeAttribute('hidden'); return; }
        data.items.forEach(article => list.appendChild(createBlogPostCard(article)));
    } catch (err) {
        console.warn('Blog: Substack feed unavailable, showing fallback —', err && err.message);
        loading?.setAttribute('hidden', '');
        error?.removeAttribute('hidden');
    }
}

if (blogSection) {
    const blogObs = new IntersectionObserver((entries) => {
        if (blogLoaded) { blogObs.disconnect(); return; }
        if (entries.some(e => e.isIntersecting)) {
            blogLoaded = true;
            blogObs.disconnect();
            fetchSubstackArticles();
        }
    }, { rootMargin: '200px' });
    blogObs.observe(blogSection);
}

/* ---------- Footer year ---------- */
$$('[data-year]').forEach(el => { el.textContent = new Date().getFullYear(); });

/* ---------- Service worker ---------- */
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js').catch(() => { /* offline support optional */ });
    });
}
