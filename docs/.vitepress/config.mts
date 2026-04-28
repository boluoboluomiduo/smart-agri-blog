import { defineConfig } from 'vitepress'
import fs from 'fs'
import path from 'path'

// 尝试加载自动生成的侧边栏配置
function loadDynamicSidebar() {
  const sidebarPath = path.resolve(__dirname, 'sidebar.json')
  if (fs.existsSync(sidebarPath)) {
    try {
      const data = JSON.parse(fs.readFileSync(sidebarPath, 'utf-8'))
      // sidebar.json 是一个数组，转换为按路径分组的对象
      const sidebar: Record<string, any[]> = {}
      const categoryMap: Record<string, string> = {
        '政策法规': '/policies/',
        '行业资讯': '/news/',
        '地方案例': '/cases/',
        '技术标准': '/standards/',
      }
      for (const group of data) {
        const route = categoryMap[group.text] || '/'
        sidebar[route] = [{
          text: group.text,
          collapsed: false,
          items: group.items,
        }]
      }
      return sidebar
    } catch {
      console.warn('侧边栏配置加载失败，使用默认配置')
    }
  }
  return null
}

// 默认侧边栏（无文章时使用）
const defaultSidebar = {
  '/policies/': [{ text: '政策法规', collapsed: false, items: [{ text: '概览', link: '/policies/' }] }],
  '/news/': [{ text: '行业资讯', collapsed: false, items: [{ text: '概览', link: '/news/' }] }],
  '/cases/': [{ text: '地方案例', collapsed: false, items: [{ text: '概览', link: '/cases/' }] }],
  '/standards/': [{ text: '技术标准', collapsed: false, items: [{ text: '概览', link: '/standards/' }] }],
}

const dynamicSidebar = loadDynamicSidebar()

export default defineConfig({
  lang: 'zh-CN',
  title: '智慧农业资讯站',
  description: '汇聚智慧农业政策法规、行业资讯、地方案例与技术标准，助力农业现代化发展',
  base: '/smart-agri-blog/',

  sitemap: {
    hostname: 'https://boluoboluomiduo.github.io/smart-agri-blog'
  },

  lastUpdated: false,

  transformPageData(pageData) {
    const path = pageData.relativePath || ''
    const isArticleList = path.endsWith('/index.md') && /^(policies|news|cases|standards)\//.test(path)
    const isArticleDetail = /\/\d{4}-\d{2}-\d{2}-/.test(path)
    
    if (isArticleList) {
      return {
        frontmatter: {
          sidebar: false,
          aside: false,
          editLink: false,
          lastUpdated: false,
          prev: false,
          next: false,
          ...pageData.frontmatter
        }
      }
    }
    
    if (isArticleDetail) {
      return {
        frontmatter: {
          sidebar: false,
          aside: false,
          editLink: false,
          lastUpdated: false,
          prev: false,
          next: false,
          ...pageData.frontmatter
        }
      }
    }
  },

  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '政策法规', link: '/policies/' },
      { text: '行业资讯', link: '/news/' },
      { text: '地方案例', link: '/cases/' },
      { text: '技术标准', link: '/standards/' },
      { text: '订阅', link: '/feed.xml', target: '_blank', noIcon: true }
    ],

    sidebar: dynamicSidebar || defaultSidebar,

    socialLinks: [
      { icon: 'github', link: 'https://github.com/boluoboluomiduo/smart-agri-blog' }
    ],

    footer: {
      message: '数据来源：农业农村部、各省农业农村厅及公开资讯渠道',
      copyright: '© 2026 智慧农业项目组 | 仅供参考，不构成任何建议'
    },

    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
          modal: {
            noResultsText: '未找到相关结果',
            resetButtonTitle: '清除查询条件',
            footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' }
          }
        }
      }
    },

    outline: { label: '页面导航' },
    docFooter: { prev: '上一篇', next: '下一篇' },
    lastUpdated: { text: '最后更新于' },
    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '菜单',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式'
  },

  head: [
    ['link', { rel: 'icon', href: '/smart-agri-blog/favicon.ico' }],
    ['meta', { name: 'theme-color', content: '#2d7a3a' }],
    // RSS Feed 链接
    ['link', { rel: 'alternate', type: 'application/rss+xml', title: '智慧农业资讯站 RSS', href: '/smart-agri-blog/feed.xml' }],
    ['link', { rel: 'alternate', type: 'application/atom+xml', title: '智慧农业资讯站 Atom', href: '/smart-agri-blog/feed-atom.xml' }],
    ['link', { rel: 'alternate', type: 'application/json', title: '智慧农业资讯站 JSON Feed', href: '/smart-agri-blog/feed.json' }]
  ]
})
