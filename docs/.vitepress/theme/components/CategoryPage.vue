<template>
  <div class="category-page">
    <ClientOnly>
      <ArticleList :articles="articles" />
    </ClientOnly>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import ArticleList from './ArticleList.vue'

// VitePress base 路径配置，与 config.mts 中的 base 保持一致
const BASE_PATH = '/smart-agri-blog/'

// 分类映射（与 utils.py CATEGORIES、config.mts categoryMap 保持一致）
const CATEGORY_MAP = {
  policies: '政策法规',
  news: '行业资讯',
  cases: '应用案例',
  standards: '技术标准'
}

const props = defineProps({
  category: {
    type: String,
    required: true
  },
  perPage: {
    type: Number,
    default: 10
  }
})

const articles = ref([])

onMounted(async () => {
  const targetLabel = CATEGORY_MAP[props.category]
  if (!targetLabel) {
    console.error(`Unknown category: ${props.category}`)
    return
  }

  try {
    const sidebarData = await import('../../sidebar.json')
    const groups = sidebarData.default
    const group = groups.find(g => g.text === targetLabel)

    if (group && group.items) {
      // 过滤掉"总览"项目，只保留文章链接，并确保所有链接以 base path 开头
      let filteredArticles = group.items
        .filter(item => !item.text.includes('总览'))
        .map(item => ({
          title: item.text,
          link: formatLink(item.link),
          date: item.date || '',
          source: item.source || '',
          description: item.description || ''
        }))
      
      // 显示所有采集的数据
      articles.value = filteredArticles
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
