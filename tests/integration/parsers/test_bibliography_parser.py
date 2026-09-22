from app.infrastructure.parsers.bibliography_parser import (
    parse_bibliographic_details,
    primary_isbn,
)


def test_parse_extended_bibliographic_fields() -> None:
    description = (
        "Кінг Д. Щоденник порнографа : роман / Денні Кінг ; "
        "[пер. з англ. Б. Превіра]. — Харків : КСД, 2025. — 248, [3] с. ; 21 см. "
        "— Перекладено за вид.: The pornographer diaries / Danny King "
        "(London : Serpent's Tail, 2004). — 3000 пр. — ISBN 978-617-15-1688-5. "
        "— ISBN 978-1-852-42861-7 (англ.) (у паліт.). — [2025-14963] "
        "УДК 821.111'06-31=161.2 К47"
    )
    details = parse_bibliographic_details(description)

    assert primary_isbn(description) == "978-617-15-1688-5"
    assert details.publication_place == "Харків"
    assert details.publisher == "КСД"
    assert details.print_run == 3000
    assert details.original_title == "The pornographer diaries"
    assert details.original_isbn == "978-1-852-42861-7"
    assert details.translators == "Б. Превіра"
