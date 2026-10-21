# Lessons

[2026-10-21] | "Ouvert" = séparation brute dès 0,5 s : 100 % des jeux open in time (le coussin des cornerbacks au snap comptait comme démarquage) | Un receveur n'est "ouvert" qu'après avoir été couvert au moins une fois (démarquage gagné). Toujours regarder la distribution d'une métrique avant de conclure.
[2026-10-21] | Test "au moins un receveur ouvert" trop permissif (un RB est presque toujours libre) | Valider la métrique sur le receveur ciblé (nom lu dans playDescription).
[2026-10-21] | Commandes PowerShell données alors que le terminal est Linux | Vérifier le shell réel ; commandes Linux pour l'utilisateur, PowerShell seulement dans le README.
[2026-10-21] | Jeu de démo "gagné" de 7,9 s, non représentatif | Filtrer les jeux de démo sur une durée réaliste (DEMO_MAX_TIME).
[2026-10-21] | Terrain de l'animation trop dézoomé (scaleanchor élargit l'axe X) | Utiliser constrain="domain" avec scaleanchor, et vérifier chaque visuel par capture.
[2026-10-21] | Pression à 0,5 s sur les QB sous le centre (défenseur déjà à ~2 yd au snap) | La pression ne compte qu'après que le QB s'est dégagé de la ligne.
[2026-10-21] | La règle "démarquage gagné" classait "jamais ouvert" un receveur jamais couvert (couverture ratée) | Un receveur jamais couvert compte comme ouvert à partir de OPEN_UNCOVERED_TIME. Tester les cas limites d'une règle (jamais couvert, toujours couvert) avant de la valider.
[2026-10-21] | `pkill -f "streamlit run app.py"` a tué le shell de la commande elle-même (le motif apparaît dans sa propre ligne) | Utiliser un motif qui ne se matche pas lui-même : `pkill -f "[s]treamlit run app"`.
[2026-10-21] | Verdict "Too late" affiché pour un receveur jamais ouvert | Distinguer les trois cas dans l'UI : open in time / too late / never open.
