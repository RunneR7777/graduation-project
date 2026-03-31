// 消息提示工具
// 基于 Vuetify 的 Snackbar 实现

interface MessageOptions {
  text: string
  color?: string
  timeout?: number
  position?: string
}

class Message {
  // 存储消息回调
  private callback: ((options: MessageOptions) => void) | null = null

  // 设置消息回调
  setCallback(callback: (options: MessageOptions) => void) {
    this.callback = callback
  }

  // 显示消息
  show(options: MessageOptions) {
    if (this.callback) {
      this.callback(options)
    } else {
      console.warn('消息回调未设置:', options.text)
    }
  }

  // 成功消息
  success(text: string, timeout = 3000) {
    this.show({
      text,
      color: 'success',
      timeout
    })
  }

  // 错误消息
  error(text: string, timeout = 5000) {
    this.show({
      text,
      color: 'error',
      timeout
    })
  }

  // 警告消息
  warning(text: string, timeout = 4000) {
    this.show({
      text,
      color: 'warning',
      timeout
    })
  }

  // 信息消息
  info(text: string, timeout = 3000) {
    this.show({
      text,
      color: 'info',
      timeout
    })
  }
}

// 创建单例
const message = new Message()

export default message
export type { MessageOptions }

