document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('div.highlight pre').forEach(function(block) {
    block.setAttribute('tabindex', '0');
  });
});
