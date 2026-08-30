/**
 * ModelShield Internationalization (i18n) Engine
 * Provides instant dynamic client-side translation across 6 languages:
 * English (en), Español (es), Français (fr), Deutsch (de), 日本語 (ja), 中文 (zh)
 */

const TRANSLATIONS = {
  en: {
    // Nav
    "nav.product": "Product",
    "nav.security": "Security Engine",
    "nav.install": "Install & Run",
    "nav.docs": "Documentation",
    "nav.github": "GitHub",
    "nav.signin": "Sign In",
    "nav.workspace": "Go to Workspace",
    "nav.returnHome": "Back to Overview",

    // Hero
    "hero.eyebrow": "MODEL VERIFICATION",
    "hero.headline": "Verify Your ML Models.",
    "hero.scroll_cue": "SCROLL TO INSPECT MODEL",

    // Spatial Callouts
    "callout.tl_title": "NEURAL GRAPH CAPTURE",
    "callout.tr_title": "92.50 (+01.75 PASS)",
    "callout.tr_label": "SECURITY SCORE",
    "callout.bl_title": "25.6M FP16 (OPTIMAL)",
    "callout.bl_label": "TENSOR WEIGHTS",
    "callout.br_title": "CLICK TO INSPECT MODEL",
    "callout.br_label": "RELEASE_GATE // VERIFIED",

    // Stages HUD
    "stage0.name": "STAGE 00 // HERO",
    "stage0.title": "Verify Your ML Models.",
    "stage1.name": "STAGE 01 // INGESTION",
    "stage1.title": "Model Weight Ingestion.",
    "stage2.name": "STAGE 02 // TOPOLOGY",
    "stage2.title": "Neural Topology Assembly.",
    "stage3.name": "STAGE 03 // SCAN",
    "stage3.title": "Volumetric Stress Scan.",
    "stage4.name": "STAGE 04 // PERTURBATION",
    "stage4.title": "Adversarial Attack Simulation.",
    "stage5.name": "STAGE 05 // VERIFICATION",
    "stage5.title": "Security Perimeter Verification.",
    "stage6.name": "STAGE 06 // DEPLOY",
    "stage6.title": "Install & Run.",

    // Platform Architecture
    "arch.eyebrow": "AI INFRASTRUCTURE SPECIFICATION",
    "arch.title": "The Complete Model Verification Stack",
    "arch.desc": "ModelShield integrates natively into your training loops and CI/CD pipelines, automatically intercepting regression anomalies and adversarial vulnerabilities before deployment.",
    "arch.view_all": "View all capabilities",
    
    // Cards
    "card1.title": "Adversarial Boundary Testing",
    "card1.desc": "Evaluates model resilience under gradient perturbation attacks (FGSM, PGD, HopSkipJump) and real-world sensor corruptions.",
    "card2.title": "Deterministic Failure Memory",
    "card2.desc": "Discovered edge-case failures are instantly crystallized into permanent regression test suites with frozen seeds and environment manifests.",
    "card3.title": "Automated CI/CD Gating",
    "card3.desc": "Strict PASS / REVIEW / BLOCK policies. Triggers GitHub Actions workflow failure when candidate accuracy drops below baseline tolerances.",
    "card4.title": "Reproducibility Verification",
    "card4.desc": "Cross-verifies model determinism across CUDA architectures, multi-GPU batching, PyTorch versions, and floating-point precision modes.",
    "card5.title": "Privacy & Membership Defense",
    "card5.desc": "Audits embedding leakage and membership inference vulnerability vectors to prevent training data reconstruction.",
    "card6.title": "Developer Inspection Workbench",
    "card6.desc": "Comprehensive web-based workspace to visually inspect layer activations, compare baseline vs candidate outputs, and approve release gates.",

    // CTA Banner
    "cta.heading": "Ready to secure your candidate models?",
    "cta.desc": "Open the ModelShield Workbench to inspect live model comparisons, run automated regression scans, and gate release deployments.",
    "cta.btn": "Open Developer Workbench",

    // Footer
    "footer.tagline": "Security & ML Regression Protection Infrastructure for Artificial Intelligence Models.",
    "footer.status": "SYSTEM OPERATIONAL // V1.0.0",
    "footer.col_platform": "PLATFORM",
    "footer.col_security": "SECURITY",
    "footer.col_resources": "RESOURCES",
    "footer.col_company": "COMPANY & POLICIES",
    "footer.link_workbench": "Developer Workbench",
    "footer.link_sec_engine": "Security Engine",
    "footer.link_verif_stack": "Verification Stack",
    "footer.link_regr_bank": "Regression Bank",
    "footer.link_adv_testing": "Adversarial Testing",
    "footer.link_repro_capsules": "Reproducibility Capsules",
    "footer.link_cicd": "CI/CD Gating",
    "footer.link_privacy_audits": "Privacy Audits",
    "footer.link_docs": "Documentation",
    "footer.link_api": "API Reference",
    "footer.link_releases": "Release Notes",
    "footer.link_status": "System Status",
    "footer.link_about": "About ModelShield",
    "footer.link_terms": "Terms of Service",
    "footer.link_privacy": "Privacy Policy",
    "footer.link_advisories": "Security Advisories",
    "footer.copyright": "© 2026 ModelShield Engineering. All rights reserved.",
    "footer.lang_label": "Language:"
  },

  es: {
    // Nav
    "nav.product": "Producto",
    "nav.security": "Motor de Seguridad",
    "nav.install": "Instalar y Ejecutar",
    "nav.docs": "Documentación",
    "nav.github": "GitHub",
    "nav.signin": "Iniciar Sesión",
    "nav.workspace": "Ir al Espacio de Trabajo",
    "nav.returnHome": "Volver a Inicio",

    // Hero
    "hero.eyebrow": "VERIFICACIÓN DE MODELOS",
    "hero.headline": "Verifica tus Modelos de IA.",
    "hero.scroll_cue": "DESPLÁZATE PARA INSPECCIONAR",

    // Spatial Callouts
    "callout.tl_title": "CAPTURA DE GRAFO NEURONAL",
    "callout.tr_title": "92.50 (+01.75 APROBADO)",
    "callout.tr_label": "PUNTUACIÓN DE SEGURIDAD",
    "callout.bl_title": "25.6M FP16 (ÓPTIMO)",
    "callout.bl_label": "PESOS TENSORES",
    "callout.br_title": "CLIC PARA INSPECCIONAR",
    "callout.br_label": "PUERTA DE LANZAMIENTO // VERIFICADA",

    // Stages HUD
    "stage0.name": "ETAPA 00 // INICIO",
    "stage0.title": "Verifica tus Modelos de IA.",
    "stage1.name": "ETAPA 01 // INGESTA",
    "stage1.title": "Ingesta de Pesos del Modelo.",
    "stage2.name": "ETAPA 02 // TOPOLOGÍA",
    "stage2.title": "Ensamblaje de Topología Neuronal.",
    "stage3.name": "ETAPA 03 // ESCANEO",
    "stage3.title": "Escaneo de Estrés Volumétrico.",
    "stage4.name": "ETAPA 04 // PERTURBACIÓN",
    "stage4.title": "Simulación de Ataque Adversario.",
    "stage5.name": "ETAPA 05 // VERIFICACIÓN",
    "stage5.title": "Verificación del Perímetro de Seguridad.",
    "stage6.name": "ETAPA 06 // DESPLIEGUE",
    "stage6.title": "Instalar y Ejecutar.",

    // Platform Architecture
    "arch.eyebrow": "ESPECIFICACIÓN DE INFRAESTRUCTURA IA",
    "arch.title": "El Stack Completo de Verificación de Modelos",
    "arch.desc": "ModelShield se integra de forma nativa en sus bucles de entrenamiento y pipelines de CI/CD, interceptando anomalías de regresión y vulnerabilidades antes del despliegue.",
    
    // Cards
    "card1.title": "Pruebas de Límites Adversarios",
    "card1.desc": "Evalúa la resiliencia del modelo ante ataques de perturbación de gradiente (FGSM, PGD, HopSkipJump) y corrupción de sensores.",
    "card2.title": "Memoria de Fallos Determinista",
    "card2.desc": "Los fallos de casos límite descubiertos se cristalizan instantáneamente en suites de pruebas de regresión permanentes con semillas fijadas.",
    "card3.title": "Compuertas Automatizadas de CI/CD",
    "card3.desc": "Políticas estrictas de APROBADO / REVISIÓN / BLOQUEO. Falla el flujo de GitHub Actions si la precisión cae por debajo de la tolerancia.",
    "card4.title": "Verificación de Reproducibilidad",
    "card4.desc": "Comprueba el determinismo en diferentes arquitecturas CUDA, procesamiento multi-GPU, versiones de PyTorch y modos de precisión FP.",
    "card5.title": "Defensa de Privacidad y Membresía",
    "card5.desc": "Audita la fuga de incrustaciones y vectores de inferencia de membresía para evitar la reconstrucción de datos de entrenamiento.",
    "card6.title": "Banco de Trabajo de Inspección",
    "card6.desc": "Espacio de trabajo web completo para inspeccionar visualmente activaciones de capas, comparar salidas y aprobar compuertas de entrega.",

    // CTA Banner
    "cta.heading": "¿Listo para asegurar sus modelos candidatos?",
    "cta.desc": "Abra ModelShield Workbench para inspeccionar comparativas de modelos en vivo, ejecutar escaneos y asegurar despliegues.",
    "cta.btn": "Abrir Banco de Trabajo",

    // Footer
    "footer.tagline": "Infraestructura de Seguridad y Protección contra Regresión de Modelos de Inteligencia Artificial.",
    "footer.status": "SISTEMA OPERATIVO // V1.0.0",
    "footer.col_platform": "PLATAFORMA",
    "footer.col_security": "SEGURIDAD",
    "footer.col_resources": "RECURSOS",
    "footer.col_company": "EMPRESA Y POLÍTICAS",
    "footer.link_workbench": "Banco de Trabajo",
    "footer.link_sec_engine": "Motor de Seguridad",
    "footer.link_verif_stack": "Stack de Verificación",
    "footer.link_regr_bank": "Banco de Regresiones",
    "footer.link_adv_testing": "Pruebas Adversarias",
    "footer.link_repro_capsules": "Cápsulas de Reproducibilidad",
    "footer.link_cicd": "Compuertas CI/CD",
    "footer.link_privacy_audits": "Auditorías de Privacidad",
    "footer.link_docs": "Documentación",
    "footer.link_api": "Referencia de API",
    "footer.link_releases": "Notas de la Versión",
    "footer.link_status": "Estado del Sistema",
    "footer.link_about": "Acerca de ModelShield",
    "footer.link_terms": "Términos de Servicio",
    "footer.link_privacy": "Política de Privacidad",
    "footer.link_advisories": "Avisos de Seguridad",
    "footer.copyright": "© 2026 ModelShield Engineering. Todos los derechos reservados.",
    "footer.lang_label": "Idioma:"
  },

  fr: {
    // Nav
    "nav.product": "Produit",
    "nav.security": "Moteur de Sécurité",
    "nav.install": "Installer & Exécuter",
    "nav.docs": "Documentation",
    "nav.github": "GitHub",
    "nav.signin": "Se Connecter",
    "nav.workspace": "Accéder à l'Espace",
    "nav.returnHome": "Retour à l'Accueil",

    // Hero
    "hero.eyebrow": "VÉRIFICATION DU MODÈLE",
    "hero.headline": "Vérifiez Vos Modèles d'IA.",
    "hero.scroll_cue": "DÉFILEZ POUR INSPECTER",

    // Spatial Callouts
    "callout.tl_title": "CAPTURE DU GRAPHE NEURONAL",
    "callout.tr_title": "92.50 (+01.75 VALIDE)",
    "callout.tr_label": "SCORE DE SÉCURITÉ",
    "callout.bl_title": "25.6M FP16 (OPTIMAL)",
    "callout.bl_label": "POIDS TENSORIELS",
    "callout.br_title": "CLIQUER POUR INSPECTER",
    "callout.br_label": "PORTE DE DÉPLOIEMENT // VALIDÉE",

    // Stages HUD
    "stage0.name": "ÉTAPE 00 // ACCUEIL",
    "stage0.title": "Vérifiez Vos Modèles d'IA.",
    "stage1.name": "ÉTAPE 01 // INGESTION",
    "stage1.title": "Ingestion des Poids du Modèle.",
    "stage2.name": "ÉTAPE 02 // TOPOLOGIE",
    "stage2.title": "Assemblage de la Topologie Neuronale.",
    "stage3.name": "ÉTAPE 03 // SCAN",
    "stage3.title": "Scan de Stress Volumétrique.",
    "stage4.name": "ÉTAPE 04 // PERTURBATION",
    "stage4.title": "Simulation d'Attaque Adversaire.",
    "stage5.name": "ÉTAPE 05 // VÉRIFICATION",
    "stage5.title": "Vérification du Périmètre de Sécurité.",
    "stage6.name": "ÉTAPE 06 // DÉPLOIEMENT",
    "stage6.title": "Installer et Exécuter.",

    // Platform Architecture
    "arch.eyebrow": "SPÉCIFICATION D'INFRASTRUCTURE IA",
    "arch.title": "La Suite Complète de Vérification de Modèles",
    "arch.desc": "ModelShield s'intègre nativement à vos boucles d'entraînement et pipelines CI/CD pour intercepter les anomalies de régression et vulnérabilités.",
    
    // Cards
    "card1.title": "Tests de Limites Adversaires",
    "card1.desc": "Évalue la résilience du modèle face aux perturbations de gradient (FGSM, PGD, HopSkipJump) et aux corruptions de capteurs.",
    "card2.title": "Mémoire Déterministe des Pannes",
    "card2.desc": "Les pannes aux cas limites sont immédiatement cristallisées en suites de régression permanentes avec graines figées.",
    "card3.title": "Contrôle Automatisé CI/CD",
    "card3.desc": "Politiques strictes de PASS / REVIEW / BLOCK. Déclenche l'échec du flux GitHub Actions en cas de baisse de précision.",
    "card4.title": "Vérification de Reproductibilité",
    "card4.desc": "Vérifie le déterminisme à travers les architectures CUDA, le multi-GPU, les versions PyTorch et les modes de précision.",
    "card5.title": "Défense de la Confidentialité",
    "card5.desc": "Audite les fuites d'embeddings et l'inférence d'appartenance pour empêcher la reconstruction des données d'entraînement.",
    "card6.title": "Établi d'Inspection Développeur",
    "card6.desc": "Espace de travail web pour inspecter visuellement les activations, comparer les sorties et approuver les mises en production.",

    // CTA Banner
    "cta.heading": "Prêt à sécuriser vos modèles candidats ?",
    "cta.desc": "Ouvrez le Workbench ModelShield pour inspecter les comparaisons en direct, lancer des scans et valider les déploiements.",
    "cta.btn": "Ouvrir l'Établi Développeur",

    // Footer
    "footer.tagline": "Infrastructure de Sécurité et de Protection contre la Régression pour Modèles d'Intelligence Artificielle.",
    "footer.status": "SYSTÈME OPÉRATIONNEL // V1.0.0",
    "footer.col_platform": "PLATEFORME",
    "footer.col_security": "SÉCURITÉ",
    "footer.col_resources": "RESSOURCES",
    "footer.col_company": "ENTREPRISE & POLITIQUES",
    "footer.link_workbench": "Établi Développeur",
    "footer.link_sec_engine": "Moteur de Sécurité",
    "footer.link_verif_stack": "Suite de Vérification",
    "footer.link_regr_bank": "Banque de Régression",
    "footer.link_adv_testing": "Tests Adversaires",
    "footer.link_repro_capsules": "Capsules de Reproductibilité",
    "footer.link_cicd": "Contrôle CI/CD",
    "footer.link_privacy_audits": "Audits de Confidentialité",
    "footer.link_docs": "Documentation",
    "footer.link_api": "Référence API",
    "footer.link_releases": "Notes de Version",
    "footer.link_status": "État du Système",
    "footer.link_about": "À Propos de ModelShield",
    "footer.link_terms": "Conditions d'Utilisation",
    "footer.link_privacy": "Politique de Confidentialité",
    "footer.link_advisories": "Avis de Sécurité",
    "footer.copyright": "© 2026 ModelShield Engineering. Tous droits réservés.",
    "footer.lang_label": "Langue :"
  },

  de: {
    // Nav
    "nav.product": "Produkt",
    "nav.security": "Sicherheits-Engine",
    "nav.install": "Installieren & Starten",
    "nav.docs": "Dokumentation",
    "nav.github": "GitHub",
    "nav.signin": "Anmelden",
    "nav.workspace": "Zum Workspace",
    "nav.returnHome": "Zurück zur Übersicht",

    // Hero
    "hero.eyebrow": "MODELLVERIFIZIERUNG",
    "hero.headline": "Verifizieren Sie Ihre KI-Modelle.",
    "hero.scroll_cue": "SCROLLEN ZUR INSPEKTION",

    // Spatial Callouts
    "callout.tl_title": "NEURONALE GRAPH-ERFASSUNG",
    "callout.tr_title": "92.50 (+01.75 BESTANDEN)",
    "callout.tr_label": "SICHERHEITS-SCORE",
    "callout.bl_title": "25.6M FP16 (OPTIMAL)",
    "callout.bl_label": "TENSOR-GEWICHTE",
    "callout.br_title": "KLICKEN ZUR INSPEKTION",
    "callout.br_label": "RELEASE-GATE // VERIFIZIERT",

    // Stages HUD
    "stage0.name": "STUFE 00 // ÜBERSICHT",
    "stage0.title": "Verifizieren Sie Ihre KI-Modelle.",
    "stage1.name": "STUFE 01 // AUFNAHME",
    "stage1.title": "Modellgewichts-Aufnahme.",
    "stage2.name": "STUFE 02 // TOPOLOGIE",
    "stage2.title": "Neuronale Topologie-Zusammenstellung.",
    "stage3.name": "STUFE 03 // SCAN",
    "stage3.title": "Volumetrischer Stresstest-Scan.",
    "stage4.name": "STUFE 04 // PERTURBATION",
    "stage4.title": "Gegnerische Angriffssimulation.",
    "stage5.name": "STUFE 05 // VERIFIKATION",
    "stage5.title": "Sicherheitsperimeter-Prüfung.",
    "stage6.name": "STUFE 06 // BEREITSTELLUNG",
    "stage6.title": "Installieren & Ausführen.",

    // Platform Architecture
    "arch.eyebrow": "KI-INFRASTRUKTUR-SPEZIFIKATION",
    "arch.title": "Der Komplette Modell-Verifikations-Stack",
    "arch.desc": "ModelShield integriert sich nativ in Trainingsschleifen und CI/CD-Pipelines, um Regressionsanomalien und Schwachstellen vor dem Release abzufangen.",
    
    // Cards
    "card1.title": "Gegnerische Grenzwertprüfung",
    "card1.desc": "Bewertet die Widerstandsfähigkeit unter Gradientenangriffen (FGSM, PGD, HopSkipJump) und Sensorstörungen.",
    "card2.title": "Deterministischer Fehlerspeicher",
    "card2.desc": "Gefundene Grenzfallfehler werden sofort in permanente Regressionstests mit eingefrorenen Seeds überführt.",
    "card3.title": "Automatisiertes CI/CD Gating",
    "card3.desc": "Strikte PASS / REVIEW / BLOCK Richtlinien. Löst GitHub Actions Fehler aus, wenn Genauigkeitsschwellen unterschritten werden.",
    "card4.title": "Reproduzierbarkeitsprüfung",
    "card4.desc": "Prüft Determinismus über CUDA-Architekturen, Multi-GPU-Setups, PyTorch-Versionen und Gleitkommamodi hinweg.",
    "card5.title": "Datenschutz- & Mitgliedschaftsabwehr",
    "card5.desc": "Prüft Embedding-Leckagen und Mitgliedschaftsinferenzvektoren zur Verhinderung der Rekonstruktion von Trainingsdaten.",
    "card6.title": "Entwickler-Inspektions-Workbench",
    "card6.desc": "Umfassender Web-Arbeitsbereich zur visuellen Inspektion von Layer-Aktivierungen und Release-Gates.",

    // CTA Banner
    "cta.heading": "Bereit, Ihre Kandidatenmodelle abzusichern?",
    "cta.desc": "Öffnen Sie die ModelShield Workbench, um Live-Modellvergleiche zu inspizieren und Releases abzusichern.",
    "cta.btn": "Entwickler-Workbench Öffnen",

    // Footer
    "footer.tagline": "Sicherheits- & Regressionsschutz-Infrastruktur für Modelle Künstlicher Intelligenz.",
    "footer.status": "SYSTEM BETRIEBSBEREIT // V1.0.0",
    "footer.col_platform": "PLATTFORM",
    "footer.col_security": "SICHERHEIT",
    "footer.col_resources": "RESSOURCEN",
    "footer.col_company": "UNTERNEHMEN & RICHTLINIEN",
    "footer.link_workbench": "Entwickler-Workbench",
    "footer.link_sec_engine": "Sicherheits-Engine",
    "footer.link_verif_stack": "Verifikations-Stack",
    "footer.link_regr_bank": "Regressions-Datenbank",
    "footer.link_adv_testing": "Gegnerische Tests",
    "footer.link_repro_capsules": "Reproduzierbarkeits-Kapseln",
    "footer.link_cicd": "CI/CD Gating",
    "footer.link_privacy_audits": "Datenschutz-Audits",
    "footer.link_docs": "Dokumentation",
    "footer.link_api": "API-Referenz",
    "footer.link_releases": "Versionshinweise",
    "footer.link_status": "Systemstatus",
    "footer.link_about": "Über ModelShield",
    "footer.link_terms": "Nutzungsbedingungen",
    "footer.link_privacy": "Datenschutzerklärung",
    "footer.link_advisories": "Sicherheitshinweise",
    "footer.copyright": "© 2026 ModelShield Engineering. Alle Rechte vorbehalten.",
    "footer.lang_label": "Sprache:"
  },

  ja: {
    // Nav
    "nav.product": "製品",
    "nav.security": "セキュリティエンジン",
    "nav.install": "インストール & 実行",
    "nav.docs": "ドキュメント",
    "nav.github": "GitHub",
    "nav.signin": "サインイン",
    "nav.workspace": "ワークスペースへ",
    "nav.returnHome": "ホームに戻る",

    // Hero
    "hero.eyebrow": "モデル検証プラットフォーム",
    "hero.headline": "機械学習モデルを検証する。",
    "hero.scroll_cue": "スクロールしてモデルを検査",

    // Spatial Callouts
    "callout.tl_title": "ニューラルグラフキャプチャ",
    "callout.tr_title": "92.50 (+01.75 合格)",
    "callout.tr_label": "セキュリティスコア",
    "callout.bl_title": "25.6M FP16 (最適)",
    "callout.bl_label": "テンソル重み",
    "callout.br_title": "クリックしてモデルを検査",
    "callout.br_label": "リリースゲート // 検証済み",

    // Stages HUD
    "stage0.name": "ステージ 00 // 概要",
    "stage0.title": "機械学習モデルを検証する。",
    "stage1.name": "ステージ 01 // 取り込み",
    "stage1.title": "モデル重みの取り込み。",
    "stage2.name": "ステージ 02 // 構造",
    "stage2.title": "ニューラル構造の構築。",
    "stage3.name": "ステージ 03 // スキャン",
    "stage3.title": "空間ストレステストスキャン。",
    "stage4.name": "ステージ 04 // 敵対的攻撃",
    "stage4.title": "敵対的攻撃シミュレーション。",
    "stage5.name": "ステージ 05 // 検証",
    "stage5.title": "セキュリティ防御壁の検証。",
    "stage6.name": "ステージ 06 // デプロイ",
    "stage6.title": "インストール＆実行。",

    // Platform Architecture
    "arch.eyebrow": "AIインフラストラクチャ仕様",
    "arch.title": "完全なモデル検証スタック",
    "arch.desc": "ModelShieldはトレーニングループとCI/CDパイプラインにネイティブ統合され、デプロイ前に回帰異常と脆弱性を自動遮断します。",
    
    // Cards
    "card1.title": "敵対的境界テスト",
    "card1.desc": "勾配摂動攻撃（FGSM、PGD、HopSkipJump）およびセンサー異常に対するモデルの堅牢性を評価します。",
    "card2.title": "決定論的障害メモリ",
    "card2.desc": "検出されたエッジケースの障害を、固定シードと環境構成を備えた恒久的な回帰テストスイートに即座に変換します。",
    "card3.title": "自動CI/CDゲーティング",
    "card3.desc": "厳格なPASS / REVIEW / BLOCKポリシー。候補モデルの精度が許容値を下回った場合にGitHub Actionsワークフローを失敗させます。",
    "card4.title": "再現性検証",
    "card4.desc": "CUDAアーキテクチャ、マルチGPUバッチ処理、PyTorchバージョン、浮動小数点モードにわたる決定論をクロス検証します。",
    "card5.title": "プライバシー＆メンバーシップ防御",
    "card5.desc": "埋め込み漏洩とメンバーシップ推論攻撃を監査し、訓練データの再構築を防止します。",
    "card6.title": "開発者インスペクションワークベンチ",
    "card6.desc": "レイヤーのアクティベーションを視覚的に検査し、ベースラインと候補出力を比較してリリースを承認する包括的ワークスペース。",

    // CTA Banner
    "cta.heading": "候補モデルを保護する準備はできましたか？",
    "cta.desc": "ModelShield Workbenchを開いて、リアルタイムのモデル比較、自動回帰スキャン、リリース制御を実行します。",
    "cta.btn": "開発者ワークベンチを開く",

    // Footer
    "footer.tagline": "人工知能モデル向けセキュリティおよび機械学習回帰保護インフラストラクチャ。",
    "footer.status": "システム正常稼働中 // V1.0.0",
    "footer.col_platform": "プラットフォーム",
    "footer.col_security": "セキュリティ",
    "footer.col_resources": "リソース",
    "footer.col_company": "企業情報・規約",
    "footer.link_workbench": "開発者ワークベンチ",
    "footer.link_sec_engine": "セキュリティエンジン",
    "footer.link_verif_stack": "検証スタック",
    "footer.link_regr_bank": "回帰テストバンク",
    "footer.link_adv_testing": "敵対的攻撃テスト",
    "footer.link_repro_capsules": "再現性カプセル",
    "footer.link_cicd": "CI/CDゲーティング",
    "footer.link_privacy_audits": "プライバシー監査",
    "footer.link_docs": "ドキュメント",
    "footer.link_api": "APIリファレンス",
    "footer.link_releases": "リリースノート",
    "footer.link_status": "システム稼働状況",
    "footer.link_about": "ModelShieldについて",
    "footer.link_terms": "利用規約",
    "footer.link_privacy": "プライバシーポリシー",
    "footer.link_advisories": "セキュリティ勧告",
    "footer.copyright": "© 2026 ModelShield Engineering. All rights reserved.",
    "footer.lang_label": "言語:"
  },

  zh: {
    // Nav
    "nav.product": "产品",
    "nav.security": "安全引擎",
    "nav.install": "安装与运行",
    "nav.docs": "文档",
    "nav.github": "GitHub",
    "nav.signin": "登录",
    "nav.workspace": "前往工作台",
    "nav.returnHome": "返回首页",

    // Hero
    "hero.eyebrow": "模型验证基础设施",
    "hero.headline": "验证您的机器学习模型。",
    "hero.scroll_cue": "向下滚动以检查模型",

    // Spatial Callouts
    "callout.tl_title": "神经网络图谱捕获",
    "callout.tr_title": "92.50 (+01.75 通过)",
    "callout.tr_label": "安全评分",
    "callout.bl_title": "25.6M FP16 (最佳)",
    "callout.bl_label": "张量权重",
    "callout.br_title": "点击检查模型",
    "callout.br_label": "发布门禁 // 已验证",

    // Stages HUD
    "stage0.name": "阶段 00 // 概览",
    "stage0.title": "验证您的机器学习模型。",
    "stage1.name": "阶段 01 // 摄取",
    "stage1.title": "模型权重摄取。",
    "stage2.name": "阶段 02 // 拓扑",
    "stage2.title": "神经拓扑组装。",
    "stage3.name": "阶段 03 // 扫描",
    "stage3.title": "空间应力测试扫描。",
    "stage4.name": "阶段 04 // 扰动",
    "stage4.title": "对抗性攻击模拟。",
    "stage5.name": "阶段 05 // 验证",
    "stage5.title": "安全防御周界验证。",
    "stage6.name": "阶段 06 // 部署",
    "stage6.title": "安装并运行。",

    // Platform Architecture
    "arch.eyebrow": "AI 基础设施规范",
    "arch.title": "完整的模型验证技术栈",
    "arch.desc": "ModelShield 原生集成到您的训练循环和 CI/CD 流水线中，在部署前自动拦截回归异常与对抗性漏洞。",
    
    // Cards
    "card1.title": "对抗边界测试",
    "card1.desc": "评估模型在梯度扰动攻击（FGSM、PGD、HopSkipJump）及真实传感器损坏下的鲁棒性。",
    "card2.title": "确定性故障记忆",
    "card2.desc": "将发现的边缘情况故障即时转化为具备冻结种子和环境清单的永久回归测试套件。",
    "card3.title": "自动化 CI/CD 门禁",
    "card3.desc": "严格的 PASS / REVIEW / BLOCK 策略。当候选模型精度低于基准阈值时触发 GitHub Actions 流水线失败。",
    "card4.title": "可复现性验证",
    "card4.desc": "跨 CUDA 架构、多 GPU 批处理、PyTorch 版本及浮点精度模式交叉验证模型确定性。",
    "card5.title": "隐私与成员推断防御",
    "card5.desc": "审计嵌入泄露与成员推断漏洞向量，防止训练数据被逆向重构。",
    "card6.title": "开发者检查工作台",
    "card6.desc": "全功能 Web 工作区，可视化检查层激活状态、对比基准与候选输出，并审批发布门禁。",

    // CTA Banner
    "cta.heading": "准备好保护您的候选模型了吗？",
    "cta.desc": "打开 ModelShield 工作台，检查实时模型对比，运行自动回归扫描并把控发布门禁。",
    "cta.btn": "打开开发者工作台",

    // Footer
    "footer.tagline": "面向人工智能模型的安全与机器学习回归防护基础设施。",
    "footer.status": "系统运行正常 // V1.0.0",
    "footer.col_platform": "平台",
    "footer.col_security": "安全",
    "footer.col_resources": "资源",
    "footer.col_company": "公司与条款",
    "footer.link_workbench": "开发者工作台",
    "footer.link_sec_engine": "安全引擎",
    "footer.link_verif_stack": "验证技术栈",
    "footer.link_regr_bank": "回归数据库",
    "footer.link_adv_testing": "对抗性测试",
    "footer.link_repro_capsules": "复现胶囊",
    "footer.link_cicd": "CI/CD 门禁",
    "footer.link_privacy_audits": "隐私审计",
    "footer.link_docs": "文档中心",
    "footer.link_api": "API 参考",
    "footer.link_releases": "版本发布说明",
    "footer.link_status": "系统状态",
    "footer.link_about": "关于 ModelShield",
    "footer.link_terms": "服务条款",
    "footer.link_privacy": "隐私政策",
    "footer.link_advisories": "安全通告",
    "footer.copyright": "© 2026 ModelShield Engineering. 保留所有权利。",
    "footer.lang_label": "语言:"
  }
};

let currentLanguage = (typeof localStorage !== "undefined" && localStorage.getItem("modelshield_lang")) || "en";

function setLanguage(lang) {
  if (!TRANSLATIONS[lang]) lang = "en";
  currentLanguage = lang;
  if (typeof localStorage !== "undefined") {
    localStorage.setItem("modelshield_lang", lang);
  }
  if (typeof document !== "undefined") {
    document.documentElement.lang = lang;

    const dict = TRANSLATIONS[lang];
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) {
        if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
          el.placeholder = dict[key];
        } else {
          el.textContent = dict[key];
        }
      }
    });

    // Sync any language selector dropdowns
    document.querySelectorAll(".lang-selector-select").forEach(sel => {
      sel.value = lang;
    });
  }

  // Dispatch event for any other scripts
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("modelshield_lang_change", { detail: { lang, dict: TRANSLATIONS[lang] } }));
  }
}

function initGlobalButtonSpotlight() {
  if (typeof document === "undefined") return;
  const animatedBtns = document.querySelectorAll(
    ".nav-btn-primary, .btn-banner-primary, .btn-morph-primary, .callout-action-btn, .btn-slider-view-all"
  );
  animatedBtns.forEach(btn => {
    btn.addEventListener("mousemove", (e) => {
      const rect = btn.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      btn.style.setProperty("--btn-mouse-x", `${x.toFixed(1)}px`);
      btn.style.setProperty("--btn-mouse-y", `${y.toFixed(1)}px`);
    });

    btn.addEventListener("click", () => {
      btn.classList.add("btn-clicked");
    });
  });
}

function initRandomFooterMascot() {
  const mascotImg = document.querySelector(".footer-agent-emoji");
  if (!mascotImg) return;

  const gifs = [
    "landing.gif",
    "idle.gif",
    "analyse.gif",
    "defence.gif",
    "reward.gif",
    "attack.gif"
  ];

  const randomGif = gifs[Math.floor(Math.random() * gifs.length)];
  const isSubpage = window.location.pathname.includes("/pages/") || (typeof document !== "undefined" && document.querySelector('link[href*="subpage.css"]') !== null);
  const basePath = isSubpage ? "../agents/gif/" : "agents/gif/";
  const fallbackPath = isSubpage ? "../agents_gif/" : "agents_gif/";

  mascotImg.src = `${basePath}${randomGif}`;
  mascotImg.onerror = function() {
    if (!this.src.includes("agents_gif")) {
      this.src = `${fallbackPath}${randomGif}`;
    }
  };

  // Interactive Easter Egg: click to roll another agent
  mascotImg.addEventListener("click", () => {
    const nextGif = gifs[Math.floor(Math.random() * gifs.length)];
    mascotImg.src = `${basePath}${nextGif}`;
    mascotImg.style.transform = "scale(1.25) rotate(12deg)";
    setTimeout(() => {
      mascotImg.style.transform = "";
    }, 250);
  });
}

function initScrollHeader() {
  if (typeof window === "undefined") return;

  let lastScrollY = window.pageYOffset || document.documentElement.scrollTop || 0;
  let ticking = false;

  window.addEventListener("scroll", () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        const currentScrollY = window.pageYOffset || document.documentElement.scrollTop || 0;
        const nav = document.querySelector(".landing-nav") || document.querySelector(".subpage-nav");
        
        if (nav) {
          if (currentScrollY <= 20) {
            // At very top
            nav.classList.remove("is-hidden");
            nav.classList.remove("is-scrolled");
          } else if (currentScrollY > lastScrollY && currentScrollY > 80) {
            // Scrolling DOWN - hide
            nav.classList.add("is-hidden");
            nav.classList.add("is-scrolled");
          } else if (currentScrollY < lastScrollY) {
            // Scrolling UP - reveal header smoothly
            nav.classList.remove("is-hidden");
            nav.classList.add("is-scrolled");
          }
        }

        lastScrollY = Math.max(0, currentScrollY);
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
}

function initLanguageEngine() {
  const savedLang = (typeof localStorage !== "undefined" && localStorage.getItem("modelshield_lang")) || "en";
  
  if (typeof document !== "undefined") {
    // Attach listeners to all language pickers
    document.querySelectorAll(".lang-selector-select").forEach(sel => {
      sel.value = savedLang;
      sel.addEventListener("change", (e) => {
        setLanguage(e.target.value);
      });
    });
  }

  setLanguage(savedLang);
  initGlobalButtonSpotlight();
  initRandomFooterMascot();
  initScrollHeader();
}

// Auto-run when DOM is ready in browser
if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initLanguageEngine);
  } else {
    initLanguageEngine();
  }
}

if (typeof window !== "undefined") {
  window.ModelShieldI18n = {
    setLanguage,
    getLanguage: () => currentLanguage,
    getDict: (lang) => TRANSLATIONS[lang || currentLanguage] || TRANSLATIONS.en,
    t: (key) => (TRANSLATIONS[currentLanguage] && TRANSLATIONS[currentLanguage][key]) || (TRANSLATIONS.en && TRANSLATIONS.en[key]) || key
  };
}
