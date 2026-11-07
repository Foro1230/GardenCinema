const menuButton = document.querySelector(".burger");
const navigation = document.querySelector("#site-navigation");

if (menuButton && navigation) {
    const setMenuOpen = (isOpen) => {
        navigation.classList.toggle("open", isOpen);
        menuButton.setAttribute("aria-expanded", String(isOpen));
        menuButton.setAttribute(
            "aria-label",
            isOpen ? "Закрити меню" : "Відкрити меню"
        );
    };

    menuButton.addEventListener("click", () => {
        const isOpen = menuButton.getAttribute("aria-expanded") === "true";
        setMenuOpen(!isOpen);
    });

    navigation.addEventListener("click", (event) => {
        if (event.target instanceof HTMLAnchorElement) {
            setMenuOpen(false);
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setMenuOpen(false);
        }
    });
}

const filmDataElement = document.querySelector("#film-data");
const previousFilmButton = document.querySelector("#previous-film");
const nextFilmButton = document.querySelector("#next-film");
const featuredTitle = document.querySelector("#featured-title");
const featuredGenre = document.querySelector("#featured-genre");
const featuredDescription = document.querySelector("#featured-description");
const featuredPoster = document.querySelector("#featured-poster");
const buyTicketLink = document.querySelector("#buy-ticket");

if (buyTicketLink && featuredTitle) {
    buyTicketLink.addEventListener("click", (event) => {
        event.preventDefault();
        const ticketUrl = new URL(buyTicketLink.href);
        ticketUrl.searchParams.set("film", featuredTitle.textContent.trim());
        window.location.assign(ticketUrl);
    });
}

if (
    filmDataElement &&
    previousFilmButton &&
    nextFilmButton &&
    featuredTitle &&
    featuredGenre &&
    featuredDescription &&
    featuredPoster
) {
    const filmsFromDatabase = JSON.parse(filmDataElement.textContent);
    const films = [
        {
            name: featuredTitle.textContent,
            genre: featuredGenre.textContent,
            description: featuredDescription.textContent,
            poster: featuredPoster.src,
        },
        ...filmsFromDatabase,
    ];
    let currentFilmIndex = 0;

    const showFilm = (index) => {
        const film = films[index];
        featuredTitle.textContent = film.name;
        featuredGenre.textContent = film.genre;
        featuredDescription.textContent = film.description || "";
        featuredDescription.hidden = !film.description;
        featuredPoster.src = film.poster || featuredPoster.dataset.defaultSrc;
        featuredPoster.alt = `Постер фільму «${film.name}»`;
        previousFilmButton.disabled = films.length < 2;
        nextFilmButton.disabled = films.length < 2;
    };

    previousFilmButton.addEventListener("click", () => {
        currentFilmIndex =
            (currentFilmIndex - 1 + films.length) % films.length;
        showFilm(currentFilmIndex);
    });

    nextFilmButton.addEventListener("click", () => {
        currentFilmIndex = (currentFilmIndex + 1) % films.length;
        showFilm(currentFilmIndex);
    });

    showFilm(currentFilmIndex);
}
