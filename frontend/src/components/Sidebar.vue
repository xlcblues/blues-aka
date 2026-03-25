<template>
  <div class="sidebar-container" :class="{ collapsed: isCollapsed }">
    <!-- 折叠按钮 - 放在侧边栏外面，独立定位 -->
    <div class="collapse-btn" @click="toggleCollapse" :class="{ 'collapsed-btn': isCollapsed }">
      <el-icon :size="20">
        <Fold v-if="!isCollapsed" />
        <Expand v-else />
      </el-icon>
    </div>

    <!-- 透明悬停触发区域 - 折叠时显示 -->
    <div
      v-if="isCollapsed"
      class="hover-trigger"
      @mouseenter="handleMouseEnter"
    >
      <!-- 临时菜单 - 悬停时显示 -->
      <transition name="slide-fade">
        <div v-if="isHovering" class="temp-sidebar" @mouseleave="handleMouseLeave">
          <div class="sidebar-logo">
            <span class="logo-icon">🐱‍👤</span>
            <span class="logo-text">Blues AKA</span>
          </div>

          <el-menu
            :default-active="activeMenu"
            class="sidebar-menu"
            router
          >
            <el-menu-item index="/agents">
              <el-icon><Avatar /></el-icon>
              <span>智能体</span>
            </el-menu-item>

            <el-menu-item index="/conversations">
              <el-icon><ChatDotRound /></el-icon>
              <span>对话列表</span>
            </el-menu-item>

            <el-menu-item index="/users" v-if="isAdmin">
              <el-icon><UserFilled /></el-icon>
              <span>用户管理</span>
            </el-menu-item>

            <el-menu-item index="/rag-metrics" v-if="isAdmin">
              <el-icon><DataAnalysis /></el-icon>
              <span>RAG性能指标</span>
            </el-menu-item>

            <el-menu-item index="/rag-index" v-if="isAdmin">
              <el-icon><FolderOpened /></el-icon>
              <span>RAG索引管理</span>
            </el-menu-item>

            <el-menu-item index="/scheduled-tasks" v-if="isAdmin">
              <el-icon><Timer /></el-icon>
              <span>定时任务管理</span>
            </el-menu-item>
          </el-menu>
        </div>
      </transition>
    </div>

    <!-- 正常侧边栏 - 展开时显示 -->
    <el-aside
      v-if="!isCollapsed"
      width="240px"
      class="sidebar"
    >
      <!-- Logo区域 -->
      <div class="sidebar-logo">
        <span class="logo-icon">🐱‍👤</span>
        <span class="logo-text">Blues AKA</span>
      </div>

      <!-- 菜单 -->
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        router
      >
        <el-menu-item index="/agents">
          <el-icon><Avatar /></el-icon>
          <span>智能体</span>
        </el-menu-item>

        <el-menu-item index="/conversations">
          <el-icon><ChatDotRound /></el-icon>
          <span>对话列表</span>
        </el-menu-item>

        <!-- 只有管理员才能看到用户管理 -->
        <el-menu-item index="/users" v-if="isAdmin">
          <el-icon><UserFilled /></el-icon>
          <span>用户管理</span>
        </el-menu-item>

        <!-- 只有管理员才能看到RAG性能指标 -->
        <el-menu-item index="/rag-metrics" v-if="isAdmin">
          <el-icon><DataAnalysis /></el-icon>
          <span>RAG性能指标</span>
        </el-menu-item>

        <!-- 只有管理员才能看到RAG索引管理 -->
        <el-menu-item index="/rag-index" v-if="isAdmin">
          <el-icon><FolderOpened /></el-icon>
          <span>RAG索引管理</span>
        </el-menu-item>

        <!-- 只有管理员才能看到定时任务管理 -->
        <el-menu-item index="/scheduled-tasks" v-if="isAdmin">
          <el-icon><Timer /></el-icon>
          <span>定时任务管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
  </div>
</template>

<script>
import { ref, computed, getCurrentInstance } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Fold, Expand, Avatar, ChatDotRound, UserFilled, DataAnalysis, FolderOpened, Timer } from '@element-plus/icons-vue'

export default {
  name: 'Sidebar',
  components: {
    Fold,
    Expand,
    Avatar,
    ChatDotRound,
    UserFilled,
    DataAnalysis,
    FolderOpened,
    Timer
  },
  emits: ['collapse-change'],
  setup() {
    const route = useRoute()
    const authStore = useAuthStore()
    const isCollapsed = ref(false)
    const isHovering = ref(false)

    // 当前激活的菜单
    const activeMenu = computed(() => {
      return route.path
    })

    // 是否为管理员
    const isAdmin = computed(() => {
      return authStore.isAdmin
    })

    // 获取当前组件实例，用于 emit
    const { emit } = getCurrentInstance()

    // 切换折叠状态
    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
      // 发出事件通知父组件
      emit('collapse-change', isCollapsed.value)
    }

    // 鼠标进入侧边栏
    const handleMouseEnter = () => {
      if (isCollapsed.value) {
        isHovering.value = true
      }
    }

    // 鼠标离开侧边栏
    const handleMouseLeave = () => {
      if (isCollapsed.value) {
        isHovering.value = false
      }
    }

    return {
      isCollapsed,
      isHovering,
      activeMenu,
      isAdmin,
      toggleCollapse,
      handleMouseEnter,
      handleMouseLeave
    }
  }
}
</script>

<style scoped>
.sidebar-container {
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 1000;
}

/* 折叠按钮 - 固定在左上角，不挡住内容 */
.collapse-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1002;
  color: white;
}

/* 折叠时的按钮样式 */
.collapsed-btn {
  position: fixed;
  left: 12px;
  top: 12px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  box-shadow: 0 4px 15px rgba(79, 70, 229, 0.5);
  z-index: 1003;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(255, 255, 255, 0.3);
}

.collapsed-btn:hover {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  transform: scale(1.15) rotate(90deg);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.6);
}

/* 悬停触发区域 - 透明区域用于触发菜单弹出 */
.hover-trigger {
  position: fixed;
  left: 0;
  top: 0;
  width: 60px; /* 扩大到60px，更容易触发 */
  height: 100vh;
  z-index: 1001;
  background: transparent; /* 改为完全透明 */
}

/* 临时菜单 - 悬停时弹出 */
.temp-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 240px;
  height: 100vh;
  background: linear-gradient(180deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%);
  box-shadow: 6px 0 30px rgba(79, 70, 229, 0.5);
  z-index: 1002;
}

/* 正常侧边栏 */
.sidebar {
  background: linear-gradient(180deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%);
  height: 100vh;
  box-shadow: 6px 0 30px rgba(79, 70, 229, 0.4);
  position: relative;
  overflow: hidden;
}

/* 滑入滑出动画 */
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s ease-in;
}

.slide-fade-enter-from {
  transform: translateX(-100%);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}

/* 临时菜单和正常侧边栏的背景纹理 */
.temp-sidebar::before,
.sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.03)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
  pointer-events: none;
  opacity: 0.5;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 10px;
  position: relative;
  z-index: 5;
}

.sidebar-logo-collapsed {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 10px;
  position: relative;
  z-index: 5;
}

.logo-icon {
  font-size: 28px;
  filter: drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.3));
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-8px);
  }
  60% {
    transform: translateY(-4px);
  }
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.5px;
}

.sidebar-menu {
  border: none;
  background: transparent;
  position: relative;
  z-index: 5;
  padding-top: 10px;
}

/* 覆盖 Element Plus 菜单样式 */
:deep(.el-menu) {
  background-color: transparent !important;
  border: none !important;
}

:deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.85) !important;
  background: transparent !important;
  border-radius: 12px;
  margin: 4px 12px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

:deep(.el-menu-item::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, #f472b6 0%, #ec4899 100%);
  transform: scaleY(0);
  transition: transform 0.3s ease;
  border-radius: 0 2px 2px 0;
}

:deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.2) !important;
  color: white !important;
  transform: translateX(6px);
  box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);
}

:deep(.el-menu-item:hover::before) {
  transform: scaleY(1);
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #f472b6 0%, #ec4899 100%) !important;
  color: white !important;
  box-shadow: 0 6px 20px rgba(236, 72, 153, 0.5);
  transform: translateX(4px) scale(1.02);
}

:deep(.el-menu-item.is-active::before) {
  transform: scaleY(1);
  background: linear-gradient(180deg, #f472b6 0%, #ec4899 100%);
}

:deep(.el-icon) {
  color: inherit !important;
  font-size: 18px;
}

/* 折叠时的样式 */
:deep(.el-menu--collapse) {
  width: 64px;
}

:deep(.el-menu--collapse .el-menu-item) {
  margin: 4px 8px;
  padding: 0;
  height: 48px;
  line-height: 48px;
  justify-content: center;
  min-width: unset;
}

:deep(.el-menu--collapse .el-menu-item .el-icon) {
  margin-right: 0;
  font-size: 20px;
}

:deep(.el-menu--collapse .el-menu-item span) {
  display: none;
}

/* 折叠时隐藏tooltip */
:deep(.el-menu--collapse .el-menu-item__title) {
  display: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
  }

  .sidebar-logo {
    padding: 15px;
  }

  .logo-text {
    font-size: 16px;
  }
}
</style>
