document.querySelectorAll('.password-toggle').forEach((button) => {
  button.addEventListener('click', () => {
    const input = button.parentElement.querySelector('input')
    const visible = input.type === 'password'
    input.type = visible ? 'text' : 'password'
    button.setAttribute('aria-label', visible ? '隐藏密码' : '显示密码')
    button.setAttribute('aria-pressed', String(visible))
  })
})

document.querySelectorAll('.preview-form').forEach((form) => {
  form.addEventListener('submit', (event) => {
    event.preventDefault()
    const notice = document.querySelector('.preview-notice')
    notice.hidden = false
    clearTimeout(window.previewNoticeTimer)
    window.previewNoticeTimer = setTimeout(() => { notice.hidden = true }, 3500)
  })
})
