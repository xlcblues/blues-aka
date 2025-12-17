<template>
  <div class="settings-container">
    <div class="page-header">
      <h1 class="page-title">⚙️ 系统设置</h1>
      <el-button @click="goBack" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
    </div>

    <div class="settings-content">
      <!-- 主题设置 -->
      <el-card class="settings-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">🎨 主题设置</span>
          </div>
        </template>

        <div class="theme-section">
          <div class="setting-item">
            <label class="setting-label">🌙 深色模式</label>
            <el-switch
              v-model="darkMode"
              @change="handleThemeChange"
              active-color="#13ce66"
              inactive-color="#ff4949"
            />
          </div>

          <div class="setting-item">
            <label class="setting-label">🎨 主题色</label>
            <div class="color-picker">
              <el-radio-group v-model="themeColor" @change="handleColorChange">
                <el-radio-button label="#4299e1">
                  <span class="color-dot" style="background: #4299e1;"></span>
                  蓝色
                </el-radio-button>
                <el-radio-button label="#48bb78">
                  <span class="color-dot" style="background: #48bb78;"></span>
                  绿色
                </el-radio-button>
                <el-radio-button label="#ed8936">
                  <span class="color-dot" style="background: #ed8936;"></span>
                  橙色
                </el-radio-button>
                <el-radio-button label="#9f7aea">
                  <span class="color-dot" style="background: #9f7aea;"></span>
                  紫色
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 通知设置 -->
      <el-card class="settings-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">🔔 通知设置</span>
          </div>
        </template>

        <div class="notification-section">
          <div class="setting-item">
            <label class="setting-label">📧 邮件通知</label>
            <el-switch
              v-model="emailNotifications"
              @change="handleNotificationChange"
              active-text="开启"
              inactive-text="关闭"
            />
          </div>

          <div class="setting-item">
            <label class="setting-label">🔊 浏览器通知</label>
            <el-switch
              v-model="browserNotifications"
              @change="handleBrowserNotificationChange"
              active-text="开启"
              inactive-text="关闭"
            />
          </div>

          <div class="setting-item">
            <label class="setting-label">📱 系统消息</label>
            <el-switch
              v-model="systemNotifications"
              @change="handleNotificationChange"
              active-text="开启"
              inactive-text="关闭"
            />
          </div>
        </div>
      </el-card>

      <!-- 语言和地区 -->
      <el-card class="settings-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">🌍 语言和地区</span>
          </div>
        </template>

        <div class="locale-section">
          <div class="setting-item">
            <label class="setting-label">🗣️ 语言</label>
            <el-select v-model="language" @change="handleLanguageChange" style="width: 200px;">
              <el-option label="简体中文" value="zh-CN" />
              <el-option label="繁體中文" value="zh-TW" />
              <el-option label="English" value="en-US" />
            </el-select>
          </div>

          <div class="setting-item">
            <label class="setting-label">🌐 时区</label>
            <el-select v-model="timezone" @change="handleTimezoneChange" style="width: 200px;">
              <el-option label="北京时间 (GMT+8)" value="Asia/Shanghai" />
              <el-option label="东京时间 (GMT+9)" value="Asia/Tokyo" />
              <el-option label="洛杉矶时间 (GMT-8)" value="America/Los_Angeles" />
              <el-option label="纽约时间 (GMT-5)" value="America/New_York" />
            </el-select>
          </div>
        </div>
      </el-card>

      <!-- 隐私设置 -->
      <el-card class="settings-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">🔒 隐私设置</span>
          </div>
        </template>

        <div class="privacy-section">
          <div class="setting-item">
            <label class="setting-label">👁️ 公开个人资料</label>
            <el-switch
              v-model="publicProfile"
              @change="handlePrivacyChange"
              active-text="公开"
              inactive-text="私密"
            />
          </div>

          <div class="setting-item">
            <label class="setting-label">📊 显示在线状态</label>
            <el-switch
              v-model="showOnlineStatus"
              @change="handlePrivacyChange"
              active-text="显示"
              inactive-text="隐藏"
            />
          </div>
        </div>
      </el-card>

      <!-- 操作按钮 -->
      <div class="settings-actions">
        <el-button type="primary" @click="saveSettings" :loading="saving" size="large">
          <el-icon><Check /></el-icon>
          保存设置
        </el-button>
        <el-button @click="resetSettings" size="large">
          <el-icon><RefreshLeft /></el-icon>
          重置默认
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

export default {
  name: 'Settings',
  setup() {
    const router = useRouter()
    const saving = ref(false)

    // 主题设置
    const darkMode = ref(false)
    const themeColor = ref('#4299e1')

    // 通知设置
    const emailNotifications = ref(true)
    const browserNotifications = ref(false)
    const systemNotifications = ref(true)

    // 语言和地区
    const language = ref('zh-CN')
    const timezone = ref('Asia/Shanghai')

    // 隐私设置
    const publicProfile = ref(false)
    const showOnlineStatus = ref(true)

    // 默认设置
    const defaultSettings = {
      darkMode: false,
      themeColor: '#4299e1',
      emailNotifications: true,
      browserNotifications: false,
      systemNotifications: true,
      language: 'zh-CN',
      timezone: 'Asia/Shanghai',
      publicProfile: false,
      showOnlineStatus: true
    }

    // 加载设置
    const loadSettings = () => {
      try {
        const savedSettings = localStorage.getItem('userSettings')
        if (savedSettings) {
          const settings = JSON.parse(savedSettings)
          Object.keys(settings).forEach(key => {
            if (key in defaultSettings) {
              if (typeof defaultSettings[key] === 'boolean') {
                if (key === 'darkMode') darkMode.value = settings[key]
                else if (key === 'emailNotifications') emailNotifications.value = settings[key]
                else if (key === 'browserNotifications') browserNotifications.value = settings[key]
                else if (key === 'systemNotifications') systemNotifications.value = settings[key]
                else if (key === 'publicProfile') publicProfile.value = settings[key]
                else if (key === 'showOnlineStatus') showOnlineStatus.value = settings[key]
              } else {
                if (key === 'themeColor') themeColor.value = settings[key]
                else if (key === 'language') language.value = settings[key]
                else if (key === 'timezone') timezone.value = settings[key]
              }
            }
          })
        }
      } catch (error) {
        console.error('加载设置失败:', error)
      }
    }

    // 保存设置
    const saveSettings = async () => {
      try {
        saving.value = true

        const settings = {
          darkMode: darkMode.value,
          themeColor: themeColor.value,
          emailNotifications: emailNotifications.value,
          browserNotifications: browserNotifications.value,
          systemNotifications: systemNotifications.value,
          language: language.value,
          timezone: timezone.value,
          publicProfile: publicProfile.value,
          showOnlineStatus: showOnlineStatus.value
        }

        localStorage.setItem('userSettings', JSON.stringify(settings))

        // 应用主题
        applyTheme()

        ElMessage.success('设置保存成功！')
      } catch (error) {
        console.error('保存设置失败:', error)
        ElMessage.error('保存设置失败，请重试')
      } finally {
        saving.value = false
      }
    }

    // 重置设置
    const resetSettings = () => {
      try {
        Object.keys(defaultSettings).forEach(key => {
          if (typeof defaultSettings[key] === 'boolean') {
            if (key === 'darkMode') darkMode.value = defaultSettings[key]
            else if (key === 'emailNotifications') emailNotifications.value = defaultSettings[key]
            else if (key === 'browserNotifications') browserNotifications.value = defaultSettings[key]
            else if (key === 'systemNotifications') systemNotifications.value = defaultSettings[key]
            else if (key === 'publicProfile') publicProfile.value = defaultSettings[key]
            else if (key === 'showOnlineStatus') showOnlineStatus.value = defaultSettings[key]
          } else {
            if (key === 'themeColor') themeColor.value = defaultSettings[key]
            else if (key === 'language') language.value = defaultSettings[key]
            else if (key === 'timezone') timezone.value = defaultSettings[key]
          }
        })

        localStorage.removeItem('userSettings')
        applyTheme()
        ElMessage.success('设置已重置为默认值')
      } catch (error) {
        console.error('重置设置失败:', error)
        ElMessage.error('重置设置失败')
      }
    }

    // 应用主题
    const applyTheme = () => {
      // 这里可以实现主题切换逻辑
      document.documentElement.style.setProperty('--primary-color', themeColor.value)

      if (darkMode.value) {
        document.body.classList.add('dark-mode')
      } else {
        document.body.classList.remove('dark-mode')
      }
    }

    // 事件处理函数
    const handleThemeChange = () => {
      applyTheme()
    }

    const handleColorChange = () => {
      applyTheme()
    }

    const handleNotificationChange = () => {
      // 处理通知设置变化
    }

    const handleBrowserNotificationChange = async () => {
      if (browserNotifications.value) {
        try {
          const permission = await Notification.requestPermission()
          if (permission !== 'granted') {
            browserNotifications.value = false
            ElMessage.warning('浏览器通知权限被拒绝')
          }
        } catch (error) {
          browserNotifications.value = false
          ElMessage.error('无法请求浏览器通知权限')
        }
      }
    }

    const handleLanguageChange = () => {
      // 处理语言变化
      ElMessage.info('语言设置已更新')
    }

    const handleTimezoneChange = () => {
      // 处理时区变化
      ElMessage.info('时区设置已更新')
    }

    const handlePrivacyChange = () => {
      // 处理隐私设置变化
    }

    // 返回上一页
    const goBack = () => {
      router.go(-1)
    }

    // 组件挂载时加载设置
    onMounted(() => {
      loadSettings()
      applyTheme()
    })

    return {
      // 数据
      darkMode,
      themeColor,
      emailNotifications,
      browserNotifications,
      systemNotifications,
      language,
      timezone,
      publicProfile,
      showOnlineStatus,
      saving,

      // 方法
      saveSettings,
      resetSettings,
      handleThemeChange,
      handleColorChange,
      handleNotificationChange,
      handleBrowserNotificationChange,
      handleLanguageChange,
      handleTimezoneChange,
      handlePrivacyChange,
      goBack
    }
  }
}
</script>

<style scoped>
.settings-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #4299e1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #2d3748;
  margin: 0;
}

.back-btn {
  color: #4299e1;
  border-color: #4299e1;
}

.back-btn:hover {
  background: rgba(66, 153, 225, 0.1);
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-card {
  border-radius: 12px;
  border: 1px solid rgba(66, 153, 225, 0.2);
  transition: all 0.3s ease;
}

.settings-card:hover {
  box-shadow: 0 8px 30px rgba(66, 153, 225, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #2d3748;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  font-size: 14px;
  font-weight: 500;
  color: #2d3748;
  min-width: 120px;
}

.color-picker {
  display: flex;
  gap: 8px;
}

.color-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}

.settings-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 30px;
  padding: 20px;
  background: rgba(66, 153, 225, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(66, 153, 225, 0.1);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .settings-container {
    padding: 10px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .setting-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .color-picker {
    flex-wrap: wrap;
  }

  .settings-actions {
    flex-direction: column;
  }
}

/* 深色模式支持 */
:deep(.dark-mode) {
  background: #1a202c;
  color: #e2e8f0;
}

:deep(.dark-mode) .settings-card {
  background: #2d3748;
  border-color: #4a5568;
}

:deep(.dark-mode) .card-title,
:deep(.dark-mode) .setting-label {
  color: #e2e8f0;
}

:deep(.dark-mode) .setting-item {
  border-color: #4a5568;
}

/* 组件样式增强 */
:deep(.el-switch__core) {
  border-radius: 20px;
}

:deep(.el-radio-button__inner) {
  border-radius: 20px;
  padding: 8px 16px;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #3182ce 0%, #2c5282 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(66, 153, 225, 0.4);
}
</style>