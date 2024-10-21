import pandas as pd
import json
import argparse

def load_pokemon_data(file_path):
    return pd.read_csv(file_path)

def top_iv_pokemon(pokemon_data, pokemon_names, is_shadow):
    filtered_data = pokemon_data[(pokemon_data['Name'].isin(pokemon_names)) & (pokemon_data['Shadow/Purified'] == is_shadow)].copy()
    
    if len(filtered_data) == 0:
        return None
    
    if 'Atk IV' in filtered_data.columns and 'Def IV' in filtered_data.columns and 'Sta IV' in filtered_data.columns:
        filtered_data['IV %'] = (filtered_data['Atk IV'] + filtered_data['Def IV'] + filtered_data['Sta IV']) / 45 * 100
        return filtered_data.loc[filtered_data['IV %'].idxmax()]
    else:
        return None


def top_3_pvp_ivs(pokemon_data, pokemon_names, is_shadow, final_stage_names, league):
    if league == 'Little':
        filtered_data = pokemon_data[
            (pokemon_data['Name'].isin(pokemon_names)) & 
            (pokemon_data['Shadow/Purified'] == is_shadow) & 
            (pokemon_data['Name (L)'] == pokemon_names[0])
        ].copy()

    elif league == 'Great':
        filtered_data = pokemon_data[
            (pokemon_data['Name'].isin(pokemon_names)) & 
            (pokemon_data['Shadow/Purified'] == is_shadow) & 
            (pokemon_data['Name (G)'].isin(final_stage_names))
        ].copy()
    elif league == 'Ultra':
        filtered_data = pokemon_data[
            (pokemon_data['Name'].isin(pokemon_names)) & 
            (pokemon_data['Shadow/Purified'] == is_shadow) & 
            (pokemon_data['Name (U)'].isin(final_stage_names))
        ].copy()
    else:
        raise ValueError(f"Unknown league: {league}")

    # Assuming the rest of your code here processes filtered_data and gets top 3 PvP IVs...


    filtered_data['Rank % (L)'] = pd.to_numeric(filtered_data['Rank % (L)'].str.rstrip('%'), errors='coerce')
    filtered_data['Rank % (G)'] = pd.to_numeric(filtered_data['Rank % (G)'].str.rstrip('%'), errors='coerce')
    filtered_data['Rank % (U)'] = pd.to_numeric(filtered_data['Rank % (U)'].str.rstrip('%'), errors='coerce')
    
    top_pokemon = {'Little': None, 'Great': None, 'Ultra': None}

    if league == 'Little' and 'Rank % (L)' in filtered_data.columns:
        top_pokemon['Little'] = filtered_data.nlargest(3, 'Rank % (L)')
    
    if league == 'Great' and 'Rank % (G)' in filtered_data.columns:
        top_pokemon['Great'] = filtered_data.nlargest(3, 'Rank % (G)')
    
    if league == 'Ultra' and 'Rank % (U)' in filtered_data.columns:
        top_pokemon['Ultra'] = filtered_data.nlargest(3, 'Rank % (U)')
    
    return top_pokemon

def earliest_caught_pokemon_by_species(pokemon_data, pokemon_names):
    filtered_data = pokemon_data[pokemon_data['Name'].isin(pokemon_names)].copy()
    filtered_data['Catch Date'] = pd.to_datetime(filtered_data['Catch Date'], errors='coerce', format='%d/%m/%Y')
    
    unique_combinations = count_name_form_combinations(pokemon_data, pokemon_names)
    
    earliest_pokemon = pd.DataFrame()
    
    for _, row in unique_combinations.iterrows():
        name, form = row['Name'], row['Form']
        if pd.isna(form):
            form_data = filtered_data[(filtered_data['Name'] == name) & (filtered_data['Form'].isna())]
        else:
            form_data = filtered_data[(filtered_data['Name'] == name) & (filtered_data['Form'] == form)]
        if not form_data.empty:
            earliest_pokemon = pd.concat([earliest_pokemon, form_data.loc[[form_data['Catch Date'].idxmin()]]])
    
    return earliest_pokemon

def count_name_form_combinations(pokemon_data, pokemon_names):
    filtered_data = pokemon_data[pokemon_data['Name'].isin(pokemon_names)].copy()
    unique_combinations = filtered_data.drop_duplicates(subset=['Name', 'Form'])[['Name', 'Form']]
    return unique_combinations

def list_pokemon_to_keep_with_reasons(pokemon_data, pokemon_names, final_stage_names):
    # Get top IV Pokémon
    top_iv_shadow = top_iv_pokemon(pokemon_data, pokemon_names, is_shadow=1)
    top_iv_non_shadow = top_iv_pokemon(pokemon_data, pokemon_names, is_shadow=0)

    # Get top 3 PvP IVs for each league for shadow and non-shadow Pokémon
    top_3_pvp_shadow_little = top_3_pvp_ivs(pokemon_data, pokemon_names, is_shadow=1, final_stage_names=final_stage_names, league='Little')
    top_3_pvp_non_shadow_little = top_3_pvp_ivs(pokemon_data, pokemon_names, is_shadow=0, final_stage_names=final_stage_names, league='Little')
    top_3_pvp_shadow_great = top_3_pvp_ivs(pokemon_data, pokemon_names, is_shadow=1, final_stage_names=final_stage_names, league='Great')
    top_3_pvp_non_shadow_great = top_3_pvp_ivs(pokemon_data, pokemon_names, is_shadow=0, final_stage_names=final_stage_names, league='Great')
    top_3_pvp_shadow_ultra = top_3_pvp_ivs(pokemon_data, pokemon_names, is_shadow=1, final_stage_names=final_stage_names, league='Ultra')
    top_3_pvp_non_shadow_ultra = top_3_pvp_ivs(pokemon_data, pokemon_names, is_shadow=0, final_stage_names=final_stage_names, league='Ultra')

    # Get the earliest caught Pokémon by species
    earliest_caught_list = earliest_caught_pokemon_by_species(pokemon_data, pokemon_names)

    reasons = []

    def add_reason(pokemon, reason):
        if pokemon is not None and pokemon.name not in [p['Name'] for p, _ in reasons]:
            reasons.append((pokemon, reason))

    add_reason(top_iv_shadow, "Top IV Shadow Pokémon")
    add_reason(top_iv_non_shadow, "Top IV Non-Shadow Pokémon")

    for league, pokemons in top_3_pvp_shadow_little.items():
        if isinstance(pokemons, pd.DataFrame):
            for _, pokemon in pokemons.iterrows():
                add_reason(pokemon, f"Top 3 PvP IVs for Little League (Shadow)")

    for league, pokemons in top_3_pvp_non_shadow_little.items():
        if isinstance(pokemons, pd.DataFrame):
            for _, pokemon in pokemons.iterrows():
                add_reason(pokemon, f"Top 3 PvP IVs for Little League (Non-Shadow)")

    for league, pokemons in top_3_pvp_shadow_great.items():
        if isinstance(pokemons, pd.DataFrame):
            for _, pokemon in pokemons.iterrows():
                add_reason(pokemon, f"Top 3 PvP IVs for Great League (Shadow)")

    for league, pokemons in top_3_pvp_non_shadow_great.items():
        if isinstance(pokemons, pd.DataFrame):
            for _, pokemon in pokemons.iterrows():
                add_reason(pokemon, f"Top 3 PvP IVs for Great League (Non-Shadow)")

    for league, pokemons in top_3_pvp_shadow_ultra.items():
        if isinstance(pokemons, pd.DataFrame):
            for _, pokemon in pokemons.iterrows():
                add_reason(pokemon, f"Top 3 PvP IVs for Ultra League (Shadow)")

    for league, pokemons in top_3_pvp_non_shadow_ultra.items():
        if isinstance(pokemons, pd.DataFrame):
            for _, pokemon in pokemons.iterrows():
                add_reason(pokemon, f"Top 3 PvP IVs for Ultra League (Non-Shadow)")

    for _, pokemon in earliest_caught_list.iterrows():
        add_reason(pokemon, "Earliest Caught Pokémon")

    return reasons

def generate_search_strings_by_pokemon(pokemon_list, character_limit=200):
    search_strings = {}

    for [pokemon, reason] in pokemon_list:
        name = pokemon['Name'].lower()
        cp = f"cp{pokemon['CP']}"

        if name not in search_strings:
            search_strings[name] = []

        current_string = search_strings[name][-1] if search_strings[name] else ""

        # Check if adding this CP value would exceed the character limit
        if len(current_string) + len(cp) + 1 > character_limit:
            search_strings[name].append(cp)
        else:
            if current_string:
                search_strings[name][-1] = f"{current_string},{cp}"
            else:
                search_strings[name].append(cp)

    formatted_search_strings = []
    for name, strings in search_strings.items():
        for s in strings:
            formatted_search_strings.append(f"{name}&{s}")

    return formatted_search_strings

def read_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def get_final_evolutions(data, evolution_line):
    final_evolutions = []
    for pokemon in evolution_line:
        if pokemon in data:
            next_evolutions = data[pokemon]
            # Check if all the evolutions in the list evolve into themselves only or are not in data
            if all(evo == pokemon or evo not in data for evo in next_evolutions):
                final_evolutions.append(pokemon.capitalize())
        else:
            final_evolutions.append(pokemon.capitalize())
    return final_evolutions

def get_evolution_lines(data, pokemon_name):
    if pokemon_name in data:
        full_line = [pokemon.capitalize() for pokemon in data[pokemon_name]]
        final_evolutions = get_final_evolutions(data, data[pokemon_name])
        return full_line, final_evolutions
    else:
        return None, None
    
data = read_json('evolutionDict.json')


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Process Pokémon data.")
    parser.add_argument('pokemon_name', type=str, help="Name of the Pokémon to analyze")
    args = parser.parse_args()

    pokemon_name = args.pokemon_name

    # Load Pokémon data
    file_path = 'poke_export.csv'
    pokemon_data = load_pokemon_data(file_path)
    
    evo_line, final_stages = get_evolution_lines(data, pokemon_name)
    if evo_line is None or final_stages is None:
        raise ValueError(f"Evolution data for Pokémon '{pokemon_name}' not found.")

    pokemon_to_keep_with_reasons = list_pokemon_to_keep_with_reasons(pokemon_data, evo_line, final_stages)

    # Display the Pokémon to keep with reasons
    df_reasons = pd.DataFrame(
        [(p['Name'], p['CP'], p['HP'], p['Catch Date'], p['Rank % (L)'], p['Rank % (G)'], p['Rank % (U)'], reason) for p, reason in pokemon_to_keep_with_reasons], 
        columns=['Name', 'CP', 'HP', 'Catch Date', 'Rank % (L)', 'Rank % (G)', 'Rank % (U)', 'Reason']
    )
    print(df_reasons)
    print(generate_search_strings_by_pokemon(pokemon_to_keep_with_reasons))

if __name__ == "__main__":
    main()
