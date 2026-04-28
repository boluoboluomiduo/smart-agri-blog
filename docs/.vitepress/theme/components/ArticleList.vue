<template>
  <div class="article-list">
    <!-- 空状态 -->
    <div v-if="articles.length === 0" class="article-list__empty">
      <span class="article-list__empty-icon">📭</span>
      <p>暂无文章</p>
    </div>

    <!-- 文章列表 -->
    <div v-else class="article-list__container">
      <a
        v-for="(item, index) in paginatedArticles"
        :key="item.link"
        :href="item.link"
        class="article-list__item"
      >
        <div class="article-list__index">{{ (currentPage - 1) * perPage + index + 1 }}</div>
        <div class="article-list__content">
          <h3 class="article-list__title">{{ item.title }}</h3>
          <div class="article-list__meta">
            <span class="article-list__date">{{ formatDate(item.date) }}</span>
            <span v-if="item.source" class="article-list__source">{{ item.source }}</span>
          </div>
          <p v-if="item.description" class="article-list__desc">{{ item.description }}</p>
        </div>
      </a>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="article-list__pagination">
      <button
        class="article-list__page-btn"
        :disabled="currentPage === 1"
        @click="goToPage(currentPage - 1)"
      >
        ← 上一页
      </button>

      <div class="article-list__page-numbers">
        <button
          v-for="page in visiblePages"
          :key="page"
          class="article-list__page-number"
          :class="{ active: page === currentPage, ellipsis: page === '...' }"
          @click="page !== '...' && goToPage(page)"
        >
          {{ page }}
        </button>
      </div>

      <button
        class="article-list__page-btn"
        :disabled="currentPage === totalPages"
        @click="goToPage(currentPage + 1)"
      >
        下一页 →
      </button>

      <span class="article-list__page-info">
        共 {{ totalPages }} 页
      </span>
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
  perPage: {
    type: Number,
    default: 15
  }
})

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

  // 始终包含首页和末页
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
.article-list {
  width: 100%;
  margin-top: 32px;
}

.article-list__container {
  display: flex;
  flex-direction: column;
  border-top: 2px solid var(--agri-border);
}

.article-list__item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 12px;
  text-decoration: none;
  color: inherit;
  border-bottom: 1px solid var(--agri-border);
  transition: background-color 0.2s ease;
}

.article-list__item:hover {
  background-color: var(--agri-green-light);
}

.article-list__index {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--agri-green-light);
  color: var(--agri-green-main);
  font-size: 13px;
  font-weight: 600;
  border-radius: 6px;
}

.article-list__content {
  flex: 1;
  min-width: 0;
}

.article-list__title {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--vp-c-text-1);
  margin: 0 0 6px;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.article-list__item:hover .article-list__title {
  color: var(--agri-green-main);
}

.article-list__meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--vp-c-text-2);
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.article-list__date {
  font-weight: 500;
  white-space: nowrap;
}

.article-list__source {
  opacity: 0.75;
  white-space: nowrap;
}

.article-list__source::before {
  content: '·';
  margin-right: 12px;
  opacity: 0.5;
}

.article-list__desc {
  font-size: 14px;
  line-height: 1.7;
  color: var(--vp-c-text-2);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.article-list__empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--vp-c-text-2);
}

.article-list__empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
}

/* 分页 */
.article-list__pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 40px;
  padding-top: 32px;
  border-top: 1px solid var(--agri-border);
  flex-wrap: wrap;
}

.article-list__page-btn {
  padding: 8px 16px;
  border: 1px solid var(--agri-border);
  border-radius: 6px;
  background-color: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
}

.article-list__page-btn:hover:not(:disabled) {
  border-color: var(--agri-green-main);
  background-color: var(--agri-green-light);
  color: var(--agri-green-main);
}

.article-list__page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.article-list__page-numbers {
  display: flex;
  gap: 6px;
  align-items: center;
}

.article-list__page-number {
  min-width: 32px;
  height: 32px;
  padding: 0 6px;
  border: 1px solid var(--agri-border);
  border-radius: 6px;
  background-color: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
}

.article-list__page-number:hover:not(.active):not(.ellipsis) {
  border-color: var(--agri-green-main);
  background-color: var(--agri-green-light);
  color: var(--agri-green-main);
}

.article-list__page-number.active {
  background-color: var(--agri-green-main);
  border-color: var(--agri-green-main);
  color: white;
  font-weight: 600;
}

.article-list__page-number.ellipsis {
  border: none;
  background: none;
  cursor: default;
  color: var(--vp-c-text-2);
  font-weight: 600;
  min-width: auto;
}

.article-list__page-info {
  font-size: 13px;
  color: var(--vp-c-text-2);
  opacity: 0.7;
}

/* 平板响应式 */
@media (max-width: 1024px) {
  .article-list__item {
    padding: 18px 10px;
    gap: 14px;
  }
}

/* 手机响应式 */
@media (max-width: 768px) {
  .article-list {
    margin-top: 24px;
  }

  .article-list__item {
    padding: 16px 8px;
    gap: 12px;
  }

  .article-list__index {
    width: 26px;
    height: 26px;
    font-size: 12px;
    border-radius: 5px;
  }

  .article-list__title {
    font-size: 15px;
    margin-bottom: 6px;
  }

  .article-list__meta {
    font-size: 12px;
    gap: 8px;
    margin-bottom: 6px;
  }

  .article-list__desc {
    font-size: 13px;
    line-height: 1.6;
    -webkit-line-clamp: 1;
  }

  .article-list__pagination {
    gap: 8px;
    margin-top: 32px;
    padding-top: 24px;
  }

  .article-list__page-btn {
    padding: 6px 12px;
    font-size: 13px;
  }

  .article-list__page-numbers {
    gap: 4px;
  }

  .article-list__page-number {
    min-width: 28px;
    height: 28px;
    font-size: 13px;
  }

  .article-list__page-info {
    font-size: 12px;
    width: 100%;
    text-align: center;
    margin-top: 4px;
  }
}

/* 小屏手机响应式 */
@media (max-width: 480px) {
  .article-list__item {
    padding: 14px 6px;
    gap: 10px;
  }

  .article-list__index {
    width: 24px;
    height: 24px;
    font-size: 11px;
  }

  .article-list__title {
    font-size: 14px;
  }

  .article-list__meta {
    font-size: 11px;
  }

  .article-list__desc {
    display: none;
  }

  .article-list__pagination {
    flex-direction: column;
    gap: 12px;
  }

  .article-list__page-numbers {
    order: -1;
  }
}
</style>
