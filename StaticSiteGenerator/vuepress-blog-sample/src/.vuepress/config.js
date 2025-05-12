module.exports = {
  base: '/blog/',
  dest: 'docs',
  // Title of your website
  title: "kapiozblog",

  // Description of your website
  description: 'This is my Engineering blog',

  head: [
    ['link', { rel: 'icon', type: 'image/png', href: '/img/favicon.png' }],
    ['link', {
      href: 'https://use.fontawesome.com/releases/v5.9.0/css/all.css',
      rel: 'stylesheet'
    }],
    ['meta', { name: 'og:url', content: 'https://kapioz.github.io/blog/' }],
    ['meta', { name: 'og:type', content: 'website' }],
    ['meta', { name: 'og:title', content: 'kapiozblog' }],
    ['meta', { name: 'og:description', content: 'This is my Engineering blog' }],
    ['meta', { name: 'og:image', content: '/img/favicon.png' }]
  ],

  // Language of your website
  locales: {
    '/': {
      lang: 'ja',
    },
  },

  // Theme to use
  theme: 'meteorlxy',

  // Theme config
  themeConfig: {

    // Language of this theme. See the [Theme Language] section below.
    lang: {
      home: 'ホーム',
      posts: '記事一覧',
      category: 'カテゴリ',
      categories: 'カテゴリ一覧',
      allCategories: 'すべて',
      tag: 'タグ',
      tags: 'タグ一覧',
      createdAt: '作成日',
      updatedAt: '更新日',
      prevPost: '前の記事',
      nextPost: '次の記事',
      toc: '目次',
      search: '検索',
      searchHint: 'タイトルから検索',
      noRelatedPosts: '関連する投稿はありません',
    },

    // Personal infomation (delete the fields if you don't have / don't want to display)
    personalInfo: {
      // Nickname
      nickname: 'kapioz',

      // Introduction of yourself
      description: 'Engineering blog',

      // Your location
      location: 'Saitama,Tokyo',

      // Your organization
      organization: 'https://qiita.com/kapioz',

      // Your avatar image
      // Set to external link
      avatar: '/blog/img/avatar.jpg',
      // Or put into `.vuepress/public` directory. E.g. `.vuepress/public/img/avatar.jpg`
      // avatar: '/img/avatar.jpg',

      // Accounts of SNS
      sns: {
        // Github account and link
        github: {
          account: 'kapioz',
          link: 'https://github.com/kapioz',
        },
        // Twitter account and link
        twitter: {
          account: '@kapioz_',
          link: 'https://twitter.com/kapioz_',
        },
        // Bitbucket account and link
        bitbucket: {
          account: 'kapioz',
          link: 'https://bitbucket.org/kapioz',
        },

      },
    },

    // Header Config
    header: {
      // The background of the header. You can choose to use an image, or to use random pattern (geopattern)
      background: {
        // URL of the background image. If you set the URL, the random pattern will not be generated, and the `useGeo` will be ignored.
        url: '/blog/img/bg.jpg',

        // Use random pattern. If you set it to `false`, and you don't set the image URL, the background will be blank.
        useGeo: true,
      },

      // show title in the header or not
      showTitle: true,
    },

    // Show the last updated time of your posts
    lastUpdated: true,

    // The content of your navbar links
    nav: [
      { text: 'ホーム', link: '/', exact: true },
      { text: '記事一覧', link: '/posts/', exact: false },
    ],

    // Comments config. See the [Posts Comments] section below.
    comments: false,

    // Pagination config
    pagination: {
      perPage: 5,
    },

    // Default Pages (Optional, the default value of all pages is `true`)
    defaultPages: {
      // Allow theme to add Home page (url: /)
      home: true,
      // Allow theme to add Posts page (url: /posts/)
      posts: true,
    },
  },
  markdown: {
    lineNumbers: true,
    anchor: {
      permalink: false
    }
  }

}