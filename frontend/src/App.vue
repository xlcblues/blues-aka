<template>
  <div id="app">
    <el-container>
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-content">
          <h1 class="logo">
            <el-icon><User /></el-icon>
            🐱‍👤 Blues AKA 用户管理系统
          </h1>
          <div class="header-nav">
            <el-button type="primary" @click="$router.push('/users')">
              <el-icon><UserFilled /></el-icon>
              用户管理
            </el-button>
          </div>
        </div>
      </el-header>

      <!-- 主要内容区域 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e8ba3 100%);
  min-height: 100vh;
}

#app {
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, #2c5282 0%, #3182ce 50%, #4299e1 100%);
  color: white;
  padding: 0;
  box-shadow: 0 4px 20px 0 rgba(49, 130, 206, 0.4);
  position: relative;
  overflow: hidden;
}

.header::before {
  content: '🎵';
  position: absolute;
  top: 10px;
  right: 80px;
  font-size: 24px;
  opacity: 0.3;
  animation: float 3s ease-in-out infinite;
}

.header::after {
  content: '🐱‍👤';
  position: absolute;
  top: 0;
  right: 20px;
  font-size: 48px;
  opacity: 0.15;
  filter: grayscale(30%);
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  position: relative;
  z-index: 2;
}

.logo {
  font-size: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  color: white;
  margin: 0;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.5px;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 15px;
}

.main-content {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 全局样式 */
.page-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(49, 130, 206, 0.15);
  border: 1px solid rgba(66, 153, 225, 0.3);
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}

.page-container::before {
  content: '🐱‍👤';
  position: absolute;
  top: 10px;
  right: 15px;
  font-size: 20px;
  opacity: 0.15;
  filter: grayscale(40%);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}
</style>