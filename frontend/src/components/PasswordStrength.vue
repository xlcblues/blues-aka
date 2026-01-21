<template>
  <div class="password-strength-indicator">
    <!-- 强度条 -->
    <div class="strength-bar">
      <div
        v-for="i in 4"
        :key="i"
        class="strength-segment"
        :class="{ active: i <= strength.score }"
        :style="{
          backgroundColor: i <= strength.score ? strength.color : '#e4e7ed'
        }"
      ></div>
    </div>

    <!-- 强度文本 -->
    <div class="strength-info">
      <span class="strength-text" :style="{ color: strength.color }">
        {{ strength.text }}
      </span>

      <!-- 详细提示（可选显示） -->
      <el-tooltip v-if="showHints && !strength.valid" effect="dark" placement="top">
        <template #content>
          <div class="strength-hints">
            <div v-for="(hint, index) in hints" :key="index" class="hint-item">
              {{ hint }}
            </div>
          </div>
        </template>
        <el-icon class="hint-icon" :style="{ color: strength.color }">
          <QuestionFilled />
        </el-icon>
      </el-tooltip>
    </div>

    <!-- 详细要求列表（可选） -->
    <div v-if="showDetails" class="strength-details">
      <div
        v-for="(check, key) in strength.checks"
        :key="key"
        class="detail-item"
        :class="{ valid: check }"
      >
        <el-icon>
          <component :is="check ? 'CircleCheck' : 'CircleClose'" />
        </el-icon>
        <span>{{ getCheckLabel(key) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { QuestionFilled, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { checkPasswordStrength, getPasswordHints } from '../utils/password'

/**
 * 密码强度指示器组件
 * 显示密码强度等级和详细要求
 */

const props = defineProps({
  // 密码值
  password: {
    type: String,
    default: ''
  },
  // 是否显示详细要求列表
  showDetails: {
    type: Boolean,
    default: false
  },
  // 是否显示悬停提示
  showHints: {
    type: Boolean,
    default: true
  }
})

// 计算密码强度
const strength = computed(() => checkPasswordStrength(props.password))

// 获取提示信息
const hints = computed(() => getPasswordHints(strength.value))

// 获取检查项的中文标签
function getCheckLabel(key) {
  const labels = {
    length: '长度至少 8 个字符',
    hasLetter: '包含字母',
    hasDigit: '包含数字',
    hasSpecial: '包含特殊字符'
  }
  return labels[key] || key
}
</script>

<style scoped lang="scss">
.password-strength-indicator {
  margin-top: 8px;
}

.strength-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}

.strength-segment {
  flex: 1;
  height: 4px;
  background-color: #e4e7ed;
  border-radius: 2px;
  transition: all 0.3s ease;

  &.active {
    transform: scaleY(1.2);
  }
}

.strength-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.strength-text {
  font-size: 12px;
  font-weight: 500;
}

.hint-icon {
  font-size: 14px;
  cursor: help;
}

.strength-hints {
  .hint-item {
    padding: 4px 0;
    font-size: 12px;
    line-height: 1.5;
  }
}

.strength-details {
  margin-top: 12px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
  color: #909399;
  transition: all 0.3s ease;

  &.valid {
    color: #67c23a;

    .el-icon {
      color: #67c23a;
    }
  }

  &:not(.valid) {
    .el-icon {
      color: #c0c4cc;
    }
  }
}
</style>
