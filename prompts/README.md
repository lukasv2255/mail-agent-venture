# prompts/

Produkční soubory které agent aktivně čte za běhu. Změna těchto souborů se projeví okamžitě při příštím `/check`.

## Soubory a kdo je čte

| Soubor                                | Čte ho                      | Popis                                               |
| ------------------------------------- | --------------------------- | --------------------------------------------------- |
| `classifier_prompt.txt`               | `src/classifier.py`         | Prompt pro klasifikaci emailů (A1/A2/B1/B2/ESC/UNK) |
| `response_a1.txt` … `response_b2.txt` | `src/responder.py`          | Šablony odpovědí pro každý typ emailu               |
| `kb_*.md`                             | `src/kb_loader.py`          | Knowledge Base — produkty, objednávky, FAQ          |
| `newsletter_format.md`                | `src/modules/newsletter.py` | Šablona formátu newsletteru                         |
| `newsletter_queries.txt`              | `src/modules/newsletter.py` | Vyhledávací dotazy pro scraping obsahu              |

## Vztah k tests/

Každý projekt má vlastní KB v `tests/<modul>/<projekt>/kb.md`.
Aby agent používal KB daného projektu, zkopíruj soubory do `prompts/`:

```
cp tests/responder/kb.md prompts/kb_projekt01.md
```
