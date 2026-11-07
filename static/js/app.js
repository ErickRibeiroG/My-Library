// My Library — interações leves (o site funciona sem JavaScript; isto só melhora a experiência).
(function () {
    'use strict';

    // ---------- Menu lateral (mobile) ----------
    document.addEventListener('click', function (evento) {
        if (evento.target.closest('[data-sidebar-abrir]')) {
            document.body.classList.add('menu-aberto');
        } else if (evento.target.closest('[data-sidebar-fechar]')) {
            document.body.classList.remove('menu-aberto');
        }
    });

    document.addEventListener('keydown', function (evento) {
        if (evento.key === 'Escape') document.body.classList.remove('menu-aberto');
    });

    // ---------- Confirmação antes de ações destrutivas ----------
    document.addEventListener('submit', function (evento) {
        var form = evento.target.closest('[data-confirmar]');
        if (form && !window.confirm(form.dataset.confirmar)) {
            evento.preventDefault();
        }
    });

    // ---------- Evita envio duplo e preserva a rolagem do trilho ----------
    document.addEventListener('submit', function (evento) {
        if (evento.defaultPrevented) return;
        var botao = evento.submitter;
        // Desabilita depois do envio começar, para o valor do botão (ex.: name="tipo") ir junto.
        if (botao) setTimeout(function () { botao.disabled = true; }, 0);
        if ((evento.target.method || '').toLowerCase() !== 'post') return;
        try {
            sessionStorage.setItem('rolagem:' + location.pathname + location.search,
                JSON.stringify({ y: window.scrollY, t: Date.now() }));
        } catch (e) { /* armazenamento indisponível */ }
    });

    // Restaura a posição da página após ações que redirecionam para ela mesma.
    try {
        var chave = 'rolagem:' + location.pathname + location.search;
        var salvo = JSON.parse(sessionStorage.getItem(chave) || 'null');
        sessionStorage.removeItem(chave);
        if (salvo && Date.now() - salvo.t < 10000) window.scrollTo(0, salvo.y || 0);
    } catch (e) { /* armazenamento indisponível */ }

    // Ao voltar pelo histórico (bfcache), reabilita botões desabilitados.
    window.addEventListener('pageshow', function () {
        document.querySelectorAll('button[disabled]').forEach(function (b) { b.disabled = false; });
    });

    // ---------- Selects que se enviam sozinhos ----------
    document.addEventListener('change', function (evento) {
        if (evento.target.matches('[data-auto-enviar]')) evento.target.form.submit();
    });

    // ---------- Capas que não carregam: mostra o placeholder ----------
    function marcarFalha(img) { img.classList.add('falhou'); }

    document.addEventListener('error', function (evento) {
        if (evento.target.matches && evento.target.matches('img[data-capa]')) marcarFalha(evento.target);
    }, true);

    document.querySelectorAll('img[data-capa]').forEach(function (img) {
        if (img.complete && img.naturalWidth === 0) marcarFalha(img);
    });

    // ---------- Mostrar / ocultar senha ----------
    document.addEventListener('click', function (evento) {
        var botao = evento.target.closest('[data-ver-senha]');
        if (!botao) return;
        var campo = botao.parentElement.querySelector('input');
        var visivel = campo.type === 'text';
        campo.type = visivel ? 'password' : 'text';
        botao.setAttribute('aria-label', visivel ? 'Mostrar senha' : 'Ocultar senha');
        botao.querySelector('i').className = visivel ? 'fa-regular fa-eye' : 'fa-regular fa-eye-slash';
    });

    // ---------- Toasts ----------
    function fecharToast(toast) {
        if (!toast || toast.classList.contains('saindo')) return;
        toast.classList.add('saindo');
        toast.addEventListener('animationend', function () { toast.remove(); }, { once: true });
    }

    document.addEventListener('click', function (evento) {
        var botao = evento.target.closest('[data-toast-fechar]');
        if (botao) fecharToast(botao.closest('[data-toast]'));
    });

    document.querySelectorAll('[data-toast]').forEach(function (toast, indice) {
        setTimeout(function () { fecharToast(toast); }, 4500 + indice * 600);
    });
})();
