document.addEventListener('DOMContentLoaded', function () {
    var galleries = document.querySelectorAll('.gallery');

    galleries.forEach(function (gallery) {
        var links = Array.prototype.slice.call(gallery.children);
        var ratios = new Array(links.length);
        var loaded = 0;

        function columnCount() {
            var w = window.innerWidth;
            if (w <= 640) return 1;
            if (w <= 900) return 2;
            return 3;
        }

        function layout() {
            var cols = columnCount();
            var colHeights = new Array(cols).fill(0);
            var colEls = [];

            gallery.classList.add('js-masonry');
            gallery.innerHTML = '';

            for (var c = 0; c < cols; c++) {
                var colDiv = document.createElement('div');
                colDiv.className = 'gallery-column';
                gallery.appendChild(colDiv);
                colEls.push(colDiv);
            }

            links.forEach(function (link, i) {
                var shortest = 0;
                for (var c = 1; c < cols; c++) {
                    if (colHeights[c] < colHeights[shortest]) shortest = c;
                }
                colEls[shortest].appendChild(link);
                colHeights[shortest] += 1 / (ratios[i] || 1);
            });
        }

        links.forEach(function (link, i) {
            var img = link.querySelector('img');
            var probe = new Image();
            probe.onload = function () {
                ratios[i] = probe.naturalWidth / probe.naturalHeight;
                loaded++;
                if (loaded === links.length) layout();
            };
            probe.onerror = function () {
                ratios[i] = 1;
                loaded++;
                if (loaded === links.length) layout();
            };
            probe.src = img.getAttribute('src');
        });

        var resizeTimer;
        window.addEventListener('resize', function () {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(layout, 150);
        });
    });
});
