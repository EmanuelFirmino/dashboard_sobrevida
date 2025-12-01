import geopandas as gpd

# 1. Carrega o shapefile original
gdf = gpd.read_file("shapes/porto_alegre.shp")

# 2. Garante que o CRS esteja definido
#    (se já estiver correto, esse bloco não altera nada)
if gdf.crs is None:
    # Ajuste aqui se necessário!
    gdf = gdf.set_crs(epsg=31983)  # exemplo — altere para o CRS correto

# 3. Reprojeta para latitude/longitude (obrigatório para mapear)
gdf_ll = gdf.to_crs(epsg=4326)

# 4. Seleciona somente 'id' e geometria
gdf_ll = gdf_ll[['id', 'geometry']]

# 5. Renomeia opcionalmente para o padrão usado no dashboard
gdf_ll = gdf_ll.rename(columns={'id': 'ID'})

# 6. Exporta para GeoJSON final
gdf_ll.to_file("bairros_poa.geojson", driver="GeoJSON", encoding="utf-8")

print("bairros_poa.geojson criado com sucesso!")
