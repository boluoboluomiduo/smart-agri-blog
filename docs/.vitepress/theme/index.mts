import DefaultTheme from 'vitepress/theme'
import { nextTick, onMounted } from 'vue'
import { inBrowser } from 'vitepress'
import './custom.css'
import ArticleList from './components/ArticleList.vue'
import ArticleListView from './components/ArticleListView.vue'
import ArticleDetailView from './components/ArticleDetailView.vue'
import Layout from './Layout.vue'

function setupExternalLinks() {
  nextTick(() => {
    const navLinks = document.querySelectorAll('.VPNavBarMenuLink, .VPNavBarMenuGroup')
    navLinks.forEach(link => {
      if (link.textContent?.includes('订阅')) {
        link.setAttribute('target', '_blank')
        link.setAttribute('rel', 'noopener noreferrer')
      }
    })
  })
}

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('ArticleList', ArticleList)
    app.component('ArticleListView', ArticleListView)
    app.component('ArticleDetailView', ArticleDetailView)
  },
  Layout,
  setup() {
    if (inBrowser) {
      onMounted(() => {
        setupExternalLinks()
      })
    }
  }
}
