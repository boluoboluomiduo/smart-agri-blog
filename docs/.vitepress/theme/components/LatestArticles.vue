<template>
  <div class="latest-articles">
    <h3 class="latest-articles__title">最新资讯</h3>
    <ul class="latest-articles__list">
      <li v-for="(article, index) in latestArticles" :key="article.link" class="latest-articles__item">
        <a :href="article.link" class="latest-articles__link">
          <span class="latest-articles__title-text">{{ article.title }}</span>
        </a>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vitepress'

// VitePress base 路径配置，与 config.mts 中的 base 保持一致
const BASE_PATH = '/smart-agri-blog/'

// 分类映射（与 utils.py CATEGORIES、config.mts categoryMap 保持一致）
const CATEGORY_MAP = {
  policies: '政策法规',
  news: '行业资讯',
  cases: '应用案例',
  standards: '技术标准'
}

const route = useRoute()
const latestArticles = ref([])

// 从当前路由获取分类
const currentCategory = computed(() => {
  const pathParts = route.path.split('/')
  return pathParts[1] // 例如：/policies/2026-04-21-标题 中的 policies
})

onMounted(async () => {
  try {
    // 直接导入sidebar.json
    const sidebarData = await import('../../sidebar.json')
    const groups = sidebarData.default
    
    // 打印当前分类和路由信息，用于调试
    console.log('Current route path:', route.path)
    console.log('Current category:', currentCategory.value)
    
    // 获取当前分类对应的标题
    const targetLabel = CATEGORY_MAP[currentCategory.value]
    if (!targetLabel) {
      console.error(`Unknown category: ${currentCategory.value}`)
      return
    }
    
    console.log('Target label:', targetLabel)
    
    // 找到当前分类的文章
    const group = groups.find(g => g.text === targetLabel)
    if (group && group.items) {
      console.log('Found group with items:', group.items.length)
      
      // 过滤掉"总览"项目，只保留文章链接，并确保所有链接以 base path 开头
      let filteredArticles = group.items
        .filter(item => !item.text.includes('总览'))
        .map(item => ({
          title: item.text.replace(/^\d+\.\s*/, ''),
          link: formatLink(item.link),
          date: item.date || '',
          source: item.source || ''
        }))
      
      console.log('Filtered articles:', filteredArticles.length)
      
      // 取最新的8条文章
      latestArticles.value = filteredArticles.slice(0, 8)
      console.log('Displaying articles:', latestArticles.value.length)
    } else {
      console.error('No articles found for category:', targetLabel)
    }
  } catch (error) {
    console.error('Failed to load sidebar data:', error)
  }
})

function formatLink(link) {
  // 如果链接已经包含完整路径则直接返回
  if (link.startsWith(BASE_PATH)) {
    return link
  }
  // 如果是相对路径或带前导斜杠的路径，添加 base path
  if (link.startsWith('/')) {
    return BASE_PATH + link.substring(1)
  }
  // 其他情况原样返回
  return link
}
</script>

<style scoped>
.latest-articles {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--agri-border);
}

.latest-articles__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--agri-green-main);
  margin-bottom: 16px;
  line-height: 1.4;
  position: relative;
  padding-left: 12px;
}

.latest-articles__title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: var(--agri-green-main);
  border-radius: 3px;
}

.latest-articles__list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.latest-articles__item {
  margin-bottom: 12px;
  position: relative;
  padding-left: 12px;
}

.latest-articles__item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  width: 3px;
  height: 3px;
  background-color: var(--agri-green-main);
  border-radius: 50%;
}

.latest-articles__link {
  text-decoration: none;
  color: var(--vp-c-text-2);
  transition: all 0.3s ease;
  font-size: 14px;
  line-height: 1.5;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.latest-articles__link:hover {
  color: var(--agri-green-main);
  transform: translateX(4px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .latest-articles {
    margin-top: 24px;
    padding-top: 20px;
  }
  
  .latest-articles__title {
    font-size: 14px;
    margin-bottom: 12px;
  }
  
  .latest-articles__item {
    margin-bottom: 8px;
  }
  
  .latest-articles__link {
    font-size: 13px;
  }
}
</style>
