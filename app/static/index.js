document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.task-done-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const btn = form.querySelector('button');
            const li = form.closest('.task-item');
            const isCurrentlyDone = li.classList.contains('completed');
            
            try {
                const res = await fetch(form.action, { 
                    method: 'POST',
                    headers: { 
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                if (res.ok) {
                    // Mise à jour visuelle instantanée
                    li.classList.toggle('completed');
                    btn.classList.toggle('completed-btn');
                    
                    const span = btn.querySelector('span');
                    span.textContent = isCurrentlyDone ? 'Done' : 'Undo';
                } else {
                    console.warn(' Réponse serveur non OK:', res.status);
                }
            } catch (err) {
                console.error(' Erreur réseau:', err);
            }
        });
    });
});