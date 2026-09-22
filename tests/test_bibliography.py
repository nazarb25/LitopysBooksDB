from litopysdb.infrastructure.bibliography import (
    parse_bibliographic_details,
    primary_isbn,
)


def test_parse_extended_bibliographic_fields():
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
    assert details.physical_description == "248, [3] с. ; 21 см"
    assert details.print_run == 3000
    assert details.catalog_number == "2025-14963"
    assert details.udc == "821.111'06-31=161.2"
    assert details.original_title == "The pornographer diaries"
    assert details.original_isbn == "978-1-852-42861-7"
    assert details.translators == "Б. Превіра"


def test_parse_contributor_roles():
    description = (
        "Назва / Автор ; [пер. з рос. К. М. Процун ; іл. А. Ю. Босенко] ; "
        "за ред. В. М. Іовенка. — Харків : Ранок, 2019. — 64 с. — 2 000 пр. "
        "— ISBN 978-617-09-5123-6. — [2019-14759] УДК 821.161.1 П64"
    )

    details = parse_bibliographic_details(description)

    assert details.translators == "К. М. Процун"
    assert details.illustrators == "А. Ю. Босенко"
    assert details.editors == "В. М. Іовенка"
