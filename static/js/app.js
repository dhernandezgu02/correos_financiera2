// Funcionalidad general de la aplicación
document.addEventListener('DOMContentLoaded', function() {
    // Auto-focus en el buscador cuando se presiona "/"
    document.addEventListener('keydown', function(e) {
        if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
            e.preventDefault();
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
    });
});
