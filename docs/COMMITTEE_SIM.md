# Yatırım Komitesi Simülasyonu (AS → ERE → PC → TE)

Bu modül, strateji çıktılarını ve risk kontrollerini bir komite akışında birleştirir:

1. **AssetSelector (AS)**: Likidite ve veri uzunluğuna göre evren seçimi  
2. **RegimeDetector**: Piyasa rejimini belirler; isteğe bağlı cap override  
3. **EnhancedRiskEngineAdapter (ERE)**: Varlık bazında izin/sizing kararı  
4. **PortfolioConstructor (PC)**: per-asset ve sektör limitleri + cash floor  
5. **TradeExecutor (TE)**: Mevcut vs hedef dağılımdan emir üretimi

Tasarım **additive** ve **non-invasive**’dir: çekirdeğe dokunmaz.
