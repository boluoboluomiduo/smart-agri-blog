<template>
  <div class="article-list-template">
    <div class="list-header">
      <h1 class="list-title">{{ categoryTitle }}</h1>
      <p class="list-subtitle">{{ categorySubtitle }}</p>
      <div class="list-stats">
        <span class="stat-item">
          <span class="stat-icon">📄</span>
          <span>共 {{ articles.length }} 篇文章</span>
        </span>
      </div>
    </div>

    <div class="list-container">
      <div v-if="articles.length === 0" class="empty-state">
        <span class="empty-icon">📭</span>
        <p>暂无文章</p>
      </div>

      <div v-else class="articles-grid">
        <a
          v-for="(item, index) in paginatedArticles"
          :key="item.link"
          :href="item.link"
          class="article-card"
        >
          <div class="card-index">{{ (currentPage - 1) * perPage + index + 1 }}</div>
          <div class="card-content">
            <div class="card-category">
              <span class="category-badge">{{ categoryTitle }}</span>
            </div>
            <h3 class="card-title">{{ item.title }}</h3>
            <div class="card-meta">
              <span v-if="item.date" class="meta-date">
                <span class="meta-icon">📅</span>
                {{ formatDate(item.date) }}
              </span>
              <span v-if="item.source" class="meta-source">
                <span class="meta-icon">📰</span>
                {{ item.source }}
              </span>
            </div>
            <p v-if="item.description" class="card-desc">{{ item.description }}</p>
          </div>
        </a>
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button
          class="page-btn"
          :disabled="currentPage === 1"
          @click.prevent="goToPage(currentPage - 1)"
        >
          ← 上一页
        </button>

        <div class="page-numbers">
          <button
            v-for="page in visiblePages"
            :key="page"
            class="page-number"
            :class="{ active: page === currentPage, ellipsis: page === '...' }"
            @click.prevent="page !== '...' && goToPage(page)"
          >
            {{ page }}
          </button>
        </div>

        <button
          class="page-btn"
          :disabled="currentPage === totalPages"
          @click.prevent="goToPage(currentPage + 1)"
        >
          下一页 →
        </button>

        <span class="page-info">
          第 {{ currentPage }} / {{ totalPages }} 页
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  articles: {
    type: Array,
    default: () => []
  },
  category: {
    type: String,
    required: true
  },
  perPage: {
    type: Number,
    default: 10
  }
})

const CATEGORY_INFO = {
  policies: {
    title: '政策法规',
    subtitle: '跟踪国家及地方智慧农业相关政策文件、规划纲要与扶持措施',
    icon: '📜'
  },
  news: {
    title: '行业资讯',
    subtitle: '聚焦智慧农业行业最新动态与前沿应用资讯',
    icon: '📰'
  },
  cases: {
    title: '地方案例',
    subtitle: '展示各地智慧农业示范项目与成功实践',
    icon: '🌾'
  },
  standards: {
    title: '技术标准',
    subtitle: '收录智慧农业领域技术规范与行业标准',
    icon: '📐'
  }
}

const categoryTitle = computed(() => CATEGORY_INFO[props.category]?.title || '文章列表')
const categorySubtitle = computed(() => CATEGORY_INFO[props.category]?.subtitle || '')

const currentPage = ref(1)

const totalPages = computed(() => {
  return Math.ceil(props.articles.length / props.perPage)
})

const paginatedArticles = computed(() => {
  const start = (currentPage.value - 1) * props.perPage
  const end = start + props.perPage
  return props.articles.slice(start, end)
})

const visiblePages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  const delta = 2

  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  let start = Math.max(1, current - delta)
  let end = Math.min(total, current + delta)

  if (start > 1) {
    start = 1
  }
  if (end < total) {
    end = total
  }

  const pages = []
  let lastPage = 0
  for (let i = start; i <= end; i++) {
    if (i - lastPage > 1 && lastPage > 0) {
      pages.push('...')
    }
    pages.push(i)
    lastPage = i
  }

  return pages
})

function goToPage(page) {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

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
</script>

<style scoped>
.article-list-template {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.list-header {
  margin-bottom: 40px;
  padding-bottom: 24px;
  border-bottom: 2px solid var(--agri-border);
}

.list-title {
  font-size: 36px;
  font-weight: 700;
  color: var(--vp-c-text-1);
  margin: 0 0 12px;
  line-height: 1.3;
}

.list-subtitle {
  font-size: 16px;
  color: var(--vp-c-text-2);
  margin: 0 0 16px;
  line-height: 1.6;
}

.list-stats {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.stat-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--vp-c-text-2);
  background: var(--agri-green-light);
  padding: 6px 12px;
  border-radius: 8px;
  font-weight: 500;
}

.stat-icon {
  font-size: 16px;
}

.list-container {
  width: 100%;
}

.articles-grid {
  display: grid;
  gap: 16px;
}

.article-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: var(--agri-card-bg);
  border: 1px solid var(--agri-border);
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--agri-shadow);
}

.article-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--agri-shadow-hover);
  border-color: var(--agri-accent);
}

.card-index {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--agri-green-main), var(--agri-accent));
  color: white;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-category {
  margin-bottom: 8px;
}

.category-badge {
  display: inline-block;
  padding: 4px 10px;
  background: var(--agri-green-light);
  color: var(--agri-green-main);
  font-size: 12px;
  font-weight: 500;
  border-radius: 4px;
}

.card-title {
  font-size: 17px;
  font-weight: 600;
  line-height: 1.5;
  color: var(--vp-c-text-1);
  margin: 0 0 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.article-card:hover .card-title {
  color: var(--agri-green-main);
}

.card-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: var(--vp-c-text-2);
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.meta-date,
.meta-source {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.meta-icon {
  font-size: 14px;
  opacity: 0.7;
}

.card-desc {
  font-size: 14px;
  line-height: 1.7;
  color: var(--vp-c-text-2);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--vp-c-text-2);
}

.empty-icon {
  font-size: 64px;
  display: block;
  margin-bottom: 16px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 48px;
  padding-top: 32px;
  border-top: 2px solid var(--agri-border);
  flex-wrap: wrap;
}

.page-btn {
  padding: 10px 20px;
  border: 1.5px solid var(--agri-border);
  border-radius: 8px;
  background: var(--agri-card-bg);
  color: var(--vp-c-text-1);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--agri-green-main);
  background: var(--agri-green-light);
  color: var(--agri-green-main);
  transform: translateY(-2px);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 8px;
  align-items: center;
}

.page-number {
  min-width: 36px;
  height: 36px;
  padding: 0 8px;
  border: 1.5px solid var(--agri-border);
  border-radius: 8px;
  background: var(--agri-card-bg);
  color: var(--vp-c-text-1);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.page-number:hover:not(.active):not(.ellipsis) {
  border-color: var(--agri-green-main);
  background: var(--agri-green-light);
  color: var(--agri-green-main);
}

.page-number.active {
  background: linear-gradient(135deg, var(--agri-green-main), var(--agri-accent));
  border-color: var(--agri-green-main);
  color: white;
  font-weight: 600;
}

.page-number.ellipsis {
  border: none;
  background: none;
  cursor: default;
  color: var(--vp-c-text-2);
  font-weight: 600;
  min-width: auto;
}

.page-info {
  font-size: 13px;
  color: var(--vp-c-text-2);
  opacity: 0.8;
}

@media (max-width: 768px) {
  .list-title {
    font-size: 28px;
  }

  .list-subtitle {
    font-size: 14px;
  }

  .article-card {
    padding: 16px;
    gap: 12px;
  }

  .card-index {
    width: 32px;
    height: 32px;
    font-size: 13px;
  }

  .card-title {
    font-size: 15px;
  }

  .card-meta {
    font-size: 12px;
    gap: 12px;
  }

  .card-desc {
    font-size: 13px;
    -webkit-line-clamp: 1;
  }

  .pagination {
    gap: 8px;
    margin-top: 32px;
    padding-top: 24px;
  }

  .page-btn {
    padding: 8px 16px;
    font-size: 13px;
  }

  .page-number {
    min-width: 32px;
    height: 32px;
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .list-header {
    margin-bottom: 24px;
    padding-bottom: 16px;
  }

  .list-title {
    font-size: 24px;
  }

  .article-card {
    padding: 14px;
    gap: 10px;
  }

  .card-index {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }

  .card-title {
    font-size: 14px;
  }

  .card-meta {
    font-size: 11px;
  }

  .card-desc {
    display: none;
  }

  .pagination {
    flex-direction: column;
    gap: 12px;
    width: 100%;
  }

  .page-numbers {
    order: -1;
    flex-wrap: wrap;
    justify-content: center;
    max-width: 100%;
  }

  .page-info {
    width: 100%;
    text-align: center;
  }
}
</style>
