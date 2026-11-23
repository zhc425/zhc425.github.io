// 蓝奏云提取码：点下载自动复制，并提示粘贴
(function () {
  function pwd(el) {
    var a = document.querySelector('a[data-pwd]');
    var b = el && el.closest && el.closest('.lz-pwd');
    var t = b && b.querySelector('[data-pwdtxt]');
    return (el && el.getAttribute && el.getAttribute('data-pwd')) || (t && t.textContent.trim()) || (a && a.getAttribute('data-pwd')) || '';
  }
  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text).catch(fallback);
    fallback();
    function fallback() {
      var ta = document.createElement('textarea'); ta.value = text; ta.setAttribute('readonly', '');
      ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); } catch (e) {} document.body.removeChild(ta);
    }
  }
  var toastEl;
  function toast(msg) {
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'lz-toast'; document.body.appendChild(toastEl); }
    toastEl.textContent = msg; toastEl.classList.add('on');
    clearTimeout(toastEl._t); toastEl._t = setTimeout(function () { toastEl.classList.remove('on'); }, 3200);
  }
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[data-pwd]');
    if (a) {
      var p = a.getAttribute('data-pwd');
      if (p) { copy(p); toast('密码 ' + p + ' 已复制，在蓝奏云页面粘贴即可'); }
      return;
    }
    var btn = e.target.closest('.lz-copy');
    if (btn) { var p2 = pwd(btn); if (p2) { copy(p2); toast('密码 ' + p2 + ' 已复制'); } }
  });
  // 无需密码时隐藏提示
  document.querySelectorAll('[data-pwdtxt]').forEach(function (b) {
    if (b.textContent.trim() === '无需密码') { var w = b.closest('.lz-pwd'); if (w) w.style.display = 'none'; }
  });
})();
