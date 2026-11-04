# value-investor-skill

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md)

## Cette action vaut-elle son prix actuel ?

Étudiez l’activité, vérifiez les hypothèses de valorisation et voyez ce que le cours suppose. Un skill de recherche pour votre assistant IA, publié par **[AhaSignals](https://ahasignals.com/methodology/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=fr_methodology)**.

[Essayer la démo dans le navigateur](https://ahasignals.com/value-investor-skill/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=fr_demo) · [Exemple avant/après](docs/demo.md) · [Licence MIT](LICENSE)

**1 skill, 5 parcours de recherche, 2 études de cas fictives, 1 illustration de démonstration et des sorties HTML, Markdown et JSON.**

![Une action fictive à 40 dollars : un même cours, des hypothèses différentes](assets/demo.svg)

### Commencer avec Claude, GPT, DeepSeek, Grok, Gemini ou Kimi

Collez les [consignes de recherche prêtes à utiliser](prompts/START_HERE.md) dans Claude, ChatGPT, DeepSeek, Grok, Gemini ou Kimi et demandez une réponse en français. Aucun terminal nécessaire. Un plugin Claude Code et une installation locale pour Codex sont également disponibles. [Guide par application](docs/hosts.md). Les outils exécutables dépendent de votre application.

### Essayez en une minute

Python 3.9 ou version ultérieure. Cette **démo fictive hors ligne** ne nécessite aucun paquet pip, aucune clé API, aucune donnée de marché payante ni aucun appel à un modèle d’IA.

```bash
git clone https://github.com/AhaSignals/value-investor-skill.git
cd value-investor-skill
python3 scripts/investor.py demo --out output/demo
```

Ouvrez `output/demo/before/research.html`, puis `output/demo/after/research.html`. Sous Windows, vous pouvez remplacer `python3` par `py -3`. Pour relancer la démo, choisissez un nouveau dossier de sortie : les recherches existantes ne sont pas écrasées.

### Installer le skill

```bash
python3 scripts/install.py --host codex
# Claude Code:
python3 scripts/install.py --host claude
```

Rechargez les skills de votre assistant, puis demandez :

> Utilise value-investor-skill pour étudier cette entreprise à partir de sources primaires. Explique en français les hypothèses nécessaires pour justifier son cours, les éléments qui les soutiennent et les preuves contraires qui modifieraient l’analyse. N’invente pas les données manquantes.

Votre assistant doit pouvoir consulter les sources ou les documents que vous fournissez. Les coûts et conditions de votre outil d’IA et de vos fournisseurs de données restent applicables. L’installateur n’écrase pas une installation existante.

### Que suppose un cours de 40 dollars ?

Ces valeurs par action sont des hypothèses fictives de valeur actualisée.

| Scénario favorable | Scénario défavorable | Pondération favorable donnant 40 dollars |
| ---: | ---: | ---: |
| 80 dollars | 20 dollars | 33,3 % |
| 60 dollars | 20 dollars | 50,0 % |

Chaque ligne correspond à un calcul distinct à deux états. **Ces pondérations ne sont ni des probabilités d’événement ni un intervalle de confiance.** La question suivante est : quelles preuves justifient 80 plutôt que 60 dollars ?

Dans la démo, si la source qui soutient le calendrier de lancement est retirée, les valorisations qui en dépendent passent à `NEEDS_REVIEW` et leurs nouveaux résultats chiffrés sont suspendus. La recherche initiale et les scénarios non concernés sont conservés.

### La méthode AhaSignals

- Séparer le cours des hypothèses économiques : changer le prix ne modifie pas les valeurs des scénarios fournis.
- Distinguer date de publication et date d’observation, et conserver les liens entre sources et calculs.
- Intégrer trésorerie, dette, coûts futurs, nouveaux capitaux et dilution dans la même valeur par action.
- Ajouter les révisions à l’historique sans effacer les jugements précédents.
- Maintenir `NOT_ESTIMATED` en l’absence de probabilité validée et `NO_QUOTE` pour l’absence de recommandation d’investissement.

Cette version calcule des scénarios et conserve les recherches. Elle ne fournit pas d’analyse automatique de tout le marché, de probabilités calibrées, de conseil personnalisé ou d’exécution d’ordres. Les métadonnées déclarées des sources ne constituent pas une authentification de leur contenu.

### Poursuivre la recherche

[Format des données](references/input-contract.md) · [Protocole de recherche](references/research-protocol.md) · [Sources et révisions chez AhaSignals](https://ahasignals.com/methodology/?utm_source=github&utm_medium=readme&utm_campaign=value_investor_launch_2026_11&utm_content=fr_methodology) · [Signaler une erreur de traduction](https://github.com/AhaSignals/value-investor-skill/issues)

Ce document est un guide de démarrage en français. La CLI, les rapports générés et la spécification détaillée restent en anglais. La langue des réponses IA dépend de l’outil utilisé. Les relectures de traduction sont les bienvenues.

AhaSignals est un éditeur de recherche indépendant. Usage de recherche et d’éducation uniquement ; aucun conseil d’investissement ou de négociation. Les noms de tiers indiquent les sources ou la compatibilité, sans affiliation ni approbation. Le code et les données fictives originales sont sous licence MIT ; les droits de redistribution des documents tiers ne sont pas accordés.
