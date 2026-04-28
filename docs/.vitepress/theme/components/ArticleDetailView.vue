<template>
  <div class="article-detail-template">
    <div class="article-header">
      <div class="article-category-badge">
        <span class="badge-icon">{{ categoryIcon }}</span>
        <span class="badge-text">{{ categoryLabel }}</span>
      </div>
      
      <h1 class="article-title">{{ title }}</h1>
      
      <div class="article-meta">
        <span v-if="date" class="meta-item meta-date">
          <span class="meta-icon">📅</span>
          <span class="meta-label">发布时间：</span>
          <span class="meta-value">{{ formatDate(date) }}</span>
        </span>
        <span v-if="source" class="meta-item meta-source">
          <span class="meta-icon">📰</span>
          <span class="meta-label">来源：</span>
          <span class="meta-value">{{ source }}</span>
        </span>
        <span v-if="lastUpdated" class="meta-item meta-updated">
          <span class="meta-icon">🔄</span>
          <span class="meta-label">更新于：</span>
          <span class="meta-value">{{ formatDate(lastUpdated) }}</span>
        </span>
      </div>

      <div v-if="tags && tags.length" class="article-tags">
        <span v-for="tag in tags" :key="tag" class="tag-item">
          {{ tag }}
        </span>
      </div>
    </div>

    <div v-if="summary" class="article-summary">
      <div class="summary-icon">💡</div>
      <div class="summary-content">
        <p>{{ summary }}</p>
      </div>
    </div>

    <div v-if="originalLink" class="article-footer">
      <div class="footer-content">
        <span class="footer-icon">🔗</span>
        <a :href="originalLink" target="_blank" rel="noopener noreferrer" class="original-link-btn">
          查看原文
        </a>
      </div>
    </div>

    <button
      v-show="showBackToTop"
      class="back-to-top-btn"
      @click="scrollToTop"
      aria-label="回到顶部"
    >
      <span class="top-icon">↑</span>
      <span class="top-text">TOP</span>
    </button>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useData } from 'vitepress'

const { frontmatter, page } = useData()

const CATEGORY_MAP = {
  policies: { label: '政策法规', icon: '📜' },
  news: { label: '行业资讯', icon: '📰' },
  cases: { label: '地方案例', icon: '🌾' },
  standards: { label: '技术标准', icon: '📐' }
}

function getCategoryFromPath() {
  const path = page.value.relativePath || ''
  const match = path.match(/^(\w+)\//)
  return match ? match[1] : ''
}

const category = computed(() => getCategoryFromPath())
const categoryLabel = computed(() => CATEGORY_MAP[category.value]?.label || '文章')
const categoryIcon = computed(() => CATEGORY_MAP[category.value]?.icon || '📄')

const title = computed(() => frontmatter.value.title || page.value.title || '')
const date = computed(() => frontmatter.value.date || '')
const source = computed(() => frontmatter.value.source || '')
const summary = computed(() => frontmatter.value.summary || '')
const tags = computed(() => frontmatter.value.tags || [])
const originalLink = computed(() => frontmatter.value.link || '')
const lastUpdated = computed(() => page.value.lastUpdated || '')

const showBackToTop = ref(false)

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  if (isNaN(date)) return dateStr
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

function handleScroll() {
  showBackToTop.value = window.scrollY > 300
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.article-detail-template {
  max-width: 900px;
  margin: 0 auto;
}

.article-header {
  margin-bottom: 40px;
  padding-bottom: 32px;
  border-bottom: 2px solid var(--agri-border);
}

.article-category-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, var(--agri-green-main), var(--agri-accent));
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 20px;
}

.badge-icon {
  font-size: 16px;
}

.article-title {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.4;
  color: var(--vp-c-text-1);
  margin: 0 0 24px;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.article-meta {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--vp-c-text-2);
  background: var(--agri-green-light);
  padding: 8px 14px;
  border-radius: 8px;
}

.meta-icon {
  font-size: 16px;
  opacity: 0.8;
}

.meta-label {
  font-weight: 500;
  opacity: 0.7;
}

.meta-value {
  font-weight: 600;
}

.article-tags {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tag-item {
  display: inline-block;
  padding: 6px 12px;
  background: var(--agri-card-bg);
  border: 1px solid var(--agri-border);
  border-radius: 6px;
  font-size: 13px;
  color: var(--vp-c-text-2);
  font-weight: 500;
}

.article-summary {
  background: linear-gradient(135deg, var(--agri-green-light), rgba(102, 187, 106, 0.1));
  border-left: 4px solid var(--agri-green-main);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 40px;
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.summary-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.summary-content {
  flex: 1;
}

.summary-content p {
  font-size: 15px;
  line-height: 1.8;
  color: var(--vp-c-text-1);
  margin: 0;
}

.article-footer {
  background: var(--agri-card-bg);
  border: 1px solid var(--agri-border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 40px;
  box-shadow: var(--agri-shadow);
}

.footer-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.footer-icon {
  font-size: 20px;
}

.original-link-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, var(--agri-green-main), var(--agri-accent));
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.original-link-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--agri-shadow-hover);
}

@media (max-width: 768px) {
  .article-title {
    font-size: 28px;
  }

  .article-meta {
    gap: 12px;
  }

  .meta-item {
    font-size: 13px;
    padding: 6px 12px;
  }

  .article-summary {
    padding: 20px;
    gap: 12px;
  }

  .summary-content p {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .article-header {
    margin-bottom: 24px;
    padding-bottom: 20px;
  }

  .article-title {
    font-size: 24px;
  }

  .article-meta {
    flex-direction: column;
    gap: 8px;
  }

  .article-tags {
    gap: 8px;
  }

  .tag-item {
    font-size: 12px;
    padding: 4px 10px;
  }

  .article-summary {
    padding: 16px;
  }

  .summary-icon {
    font-size: 20px;
  }

  .summary-content p {
    font-size: 13px;
    line-height: 1.6;
  }
}

.back-to-top-btn {
  position: fixed;
  bottom: 40px;
  right: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, var(--agri-green-main), var(--agri-accent));
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(45, 122, 58, 0.4);
  transition: all 0.3s ease;
  z-index: 100;
}

.back-to-top-btn:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 20px rgba(45, 122, 58, 0.5);
}

.back-to-top-btn:active {
  transform: translateY(-2px);
}

.top-icon {
  font-size: 20px;
  font-weight: bold;
  line-height: 1;
}

.top-text {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

@media (max-width: 768px) {
  .back-to-top-btn {
    bottom: 24px;
    right: 24px;
    width: 48px;
    height: 48px;
  }

  .top-icon {
    font-size: 18px;
  }

  .top-text {
    font-size: 11px;
  }
}
</style>
