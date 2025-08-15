# python con REST API
# Requiere: pip install requests
import requests

POKEMONS = {
    1: "pichu",
    2: "charmander",
    3: "squirtle",
    4: "bulbasaur",
}

# Colores exigidos por tipo
STYLE_BY_TYPE = {
    "fire": {"bg": "#d62828", "fg": "white"},
    "water": {"bg": "#1d4ed8", "fg": "white"},
    "electric": {"bg": "#fde047", "fg": "#000000"},
    "grass": {"bg": "#22c55e", "fg": "#000000"},
}

API = "https://pokeapi.co/api/v2"


def get_json(url: str):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def pick_effect_text(effect_entries):
    """
    Devuelve una cadena con el efecto de la habilidad.
    Preferimos 'effect'; en inglés,
    si no hay inglés, tomamos el primer idioma disponible.
    """
    if not effect_entries:
        return "No effect text."
    # Buscar en inglés
    for e in effect_entries:
        if e.get("language", {}).get("name") == "en":
            return e.get("effect") or "No effect text."
    # Fallback al primero disponible
    e = effect_entries[0]
    return e.get("effect") or "No effect text."


def get_ability_with_effects(abilities):
    """
    abilities: lista de objetos abilities del endpoint /pokemon/<name>
    Regresa lista de dicts: [{name, effect}]
    """
    out = []
    for a in abilities:
        a_name = a["ability"]["name"]
        a_url = a["ability"]["url"]
        try:
            a_data = get_json(a_url)
            effect = pick_effect_text(a_data.get("effect_entries", []))
        except Exception:
            effect = "Effect unavailable."
        out.append({"name": a_name, "effect": effect})
    return out


def get_types_damage(type_name: str):
    """
    type_name: recibe el nombre de un tipo de pokemon 
    Regresa dos listas:
    to_double -> tipos a los que hace daño doble
    from_double -> tipos de los que recibe daño doble
    """
    t = get_json(f"{API}/type/{type_name}")
    rel = t["damage_relations"]
    to_double = [x["name"] for x in rel["double_damage_to"]]
    from_double = [x["name"] for x in rel["double_damage_from"]]
    return to_double, from_double


def get_evolution_chain(species_url: str):
    """
    Devuelve lista con el orden de la cadena de evolución, e.g.
    ['bulbasaur', 'ivysaur', 'venusaur']
    """
    species = get_json(species_url)
    evo_url = species["evolution_chain"]["url"]
    chain_data = get_json(evo_url)

    order = []
    node = chain_data["chain"]
    while node:
        order.append(node["species"]["name"])
        node = node["evolves_to"][0] if node["evolves_to"] else None
    return order


def choose_style(types):
    """
    Selecciona el esquema de colores según el tipo principal
    (fire/water/electric/grass). Si no coincide, usa tema neutro.
    """
    primary = types[0]["type"]["name"]
    style = STYLE_BY_TYPE.get(
        primary, {}
    )
    return primary, style


def build_html(poke):
    """
    Recibe el JSON del endpoint /pokemon/name
    Devuelve un archivo .html 
    """
    name = poke["name"].title()

    # Imagen 
    sprites = poke.get("sprites", {})
    sprite = (
    sprites.get("front_female") or
    sprites.get("front_shiny")  or
    sprites.get("front_default") or
    ""  # si ninguna existe
    )

    # Tipos
    types = poke["types"]
    type_names = [t["type"]["name"] for t in types]
    primary_type, style = choose_style(types)

    # Stats principales
    stats = {s["stat"]["name"]: s["base_stat"] for s in poke["stats"]}
    hp = stats.get("hp", "?")
    atk = stats.get("attack", "?")
    deff = stats.get("defense", "?")
    base_exp = poke.get("base_experience", "?")

    # Abilidades + efecto
    abilities = get_ability_with_effects(poke["abilities"])

    # Evoluciones (2da y 3ra etapa)
    evo_order = get_evolution_chain(poke["species"]["url"])
    try:
        idx_self = evo_order.index(poke["name"])
        evolves_next = evo_order[idx_self + 1 : idx_self + 3]
    except ValueError:
        evolves_next = evo_order[1:3]  # fallback si no lo encuentra

    # Doble daño (a / de)
    dd_to, dd_from = get_types_damage(primary_type)

    # HTML
    ability_items = "\n".join(
        f"<li><b>{(a['name'].title())}:</b> {(a['effect'])}</li>"
        for a in abilities
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{name}</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  :root {{
    --bg: {style['bg']};
    --fg: {style['fg']};
    --card: rgba(255,255,255,0.15);
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 2rem;
    background: var(--bg);
    color: var(--fg);
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    line-height: 1.45;
  }}
  h1 {{ margin-top: 0; font-size: 2.25rem; }}
  .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); gap: 1rem; }}
  .img-wrap {{ text-align: center; }}
  img {{ width: 320px; max-width: 90%; height: auto; filter: drop-shadow(0 12px 18px rgba(0,0,0,.3)); }}
  ul {{ padding-left: 1.2rem; }}
  .tag {{ display:inline-block; padding:.2rem .6rem; border-radius:999px; border:1px solid rgba(0,0,0,.1); margin-right:.35rem; background: rgba(255,255,255,.25); }}
  .section {{ margin-top: 1.25rem; }}
  code {{ background: rgba(0,0,0,.15); padding: .1rem .35rem; border-radius: 6px; }}
</style>
</head>
<body>
  <div>
    <h1>{name}</h1>
    <div class="img-wrap">
      <img src="{(sprite or '')}" alt="{name}">
    </div>

    <div class="meta">
      <div><b>Type:</b> {' , '.join(t.title() for t in type_names)}</div>
      <div><b>Base Experience:</b> {base_exp}</div>
      <div><b>HP:</b> {hp}</div>
      <div><b>Attack:</b> {atk}</div>
      <div><b>Defense:</b> {deff}</div>
    </div>

    <div class="section">
      <h2>Abilities & Effects</h2>
      <ul>
        {ability_items}
      </ul>
    </div>

    <div class="section">
      <h2>Evolves to</h2>
      <p>{', '.join(e.title() for e in evolves_next) if evolves_next else 'No further evolutions.'}</p>
    </div>

    <div class="section">
      <h2>Double Damage</h2>
      <p><b>Deals 2× to:</b> {' , '.join(x.title() for x in dd_to) or '—'}</p>
      <p><b>Takes 2× from:</b> {' , '.join(x.title() for x in dd_from) or '—'}</p>
    </div>

  </div>
</body>
</html>
"""
    return html


def main():
    print("Elige un Pokémon:\n1) Pichu\n2) Charmander\n3) Squirtle\n4) Bulbasaur")
    try:
        choice = int(input("> ").strip())
        if choice not in POKEMONS:
            raise ValueError
    except Exception:
        print("Opción inválida. Debe ser 1–4.")
        return

    name = POKEMONS[choice]
    print(f"Descargando datos de {name.title()}...")
    poke = get_json(f"{API}/pokemon/{name}")
    html = build_html(poke)

    out_name = f"{name}.html"
    with open(out_name, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Archivo generado: {out_name}")


if __name__ == "__main__":
    main()
