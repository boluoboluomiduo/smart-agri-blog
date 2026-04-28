<template>
  <DefaultTheme.Layout>
    <template #doc-before>
      <ArticleListView
        v-if="shouldShowListView"
        :articles="listArticles"
        :category="currentCategory"
        :per-page="10"
      />
      <ArticleDetailView
        v-else-if="shouldShowDetailView"
      />
    </template>
  </DefaultTheme.Layout>
</template>

<script setup>
import DefaultTheme from 'vitepress/theme'
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useData, useRoute } from 'vitepress'
import ArticleListView from './components/ArticleListView.vue'
import ArticleDetailView from './components/ArticleDetailView.vue'

const { frontmatter, page } = useData()
const route = useRoute()

const listArticles = ref([])
const currentCategory = ref('')

const CATEGORY_MAP = {
  policies: '政策法规',
  news: '行业资讯',
  cases: '应用案例',
  standards: '技术标准'
}

const BASE_PATH = '/smart-agri-blog/'

const shouldShowListView = computed(() => {
  const path = page.value.relativePath || ''
  const isIndex = path.endsWith('/index.md')
  const hasCategory = Object.keys(CATEGORY_MAP).some(cat => path.startsWith(`${cat}/`))
  return isIndex && hasCategory
})

const shouldShowDetailView = computed(() => {
  const path = page.value.relativePath || ''
  return /\/\d{4}-\d{2}-\d{2}-/.test(path)
})

function getCurrentCategory() {
  const path = page.value.relativePath || ''
  return Object.keys(CATEGORY_MAP).find(cat => path.startsWith(`${cat}/`)) || ''
}

// 动态设置导航栏的active状态
function setActiveNavLink() {
  nextTick(() => {
    const category = getCurrentCategory()
    
    const navLinks = document.querySelectorAll('.VPNavBarMenuLink')
    navLinks.forEach(link => {
      const text = link.textContent || ''
      link.classList.remove('active')
      
      if (!category) {
        // 在首页时，将首页链接设为active
        if (text === '首页') {
          link.classList.add('active')
        }
      } else {
        // 根据当前文章的分类设置对应的导航链接为active
        if (text.includes(CATEGORY_MAP[category])) {
          link.classList.add('active')
        }
      }
    })
  })
}

async function loadArticles(category) {
  if (!category) {
    listArticles.value = []
    return
  }

  const targetLabel = CATEGORY_MAP[category]
  if (!targetLabel) {
    listArticles.value = []
    return
  }

  try {
    const sidebarData = await import('../sidebar.json')
    const groups = sidebarData.default
    const group = groups.find(g => g.text === targetLabel)

    if (group && group.items) {
      listArticles.value = group.items
        .filter(item => !item.text.includes('总览'))
        .map(item => ({
          title: item.text,
          link: formatLink(item.link),
          date: item.date || '',
          source: item.source || '',
          description: item.description || ''
        }))
    }
  } catch (error) {
    console.error('Failed to load sidebar data:', error)
    listArticles.value = []
  }
}

function formatLink(link) {
  if (link.startsWith(BASE_PATH)) {
    return link
  }
  if (link.startsWith('/')) {
    return BASE_PATH + link.substring(1)
  }
  return link
}

watch(() => route.path, async () => {
  currentCategory.value = getCurrentCategory()
  
  if (shouldShowListView.value) {
    await loadArticles(currentCategory.value)
  } else {
    listArticles.value = []
  }
  
  // 设置导航栏active状态
  setActiveNavLink()
}, { immediate: true })

onMounted(async () => {
  currentCategory.value = getCurrentCategory()
  
  if (shouldShowListView.value) {
    await loadArticles(currentCategory.value)
  } else {
    listArticles.value = []
  }
  
  // 设置导航栏active状态
  setActiveNavLink()
})
</script>
