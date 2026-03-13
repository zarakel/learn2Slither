"""
Module interactif de configuration pour Learn2Slither.

Lance une session de questions/réponses où les questions de suivi sont
générées dynamiquement selon les réponses de l'utilisateur.
Invoquer via : python main.py load ask
"""


class AskSession:
    """Session interactive de configuration guidée de l'entraînement."""

    QUESTIONS = {
        'sessions': (
            "Combien de sessions d'entraînement voulez-vous effectuer ?"
        ),
        'load': (
            "Voulez-vous charger un modèle existant ? "
            "(chemin du fichier ou 'non')"
        ),
        'save': (
            "Voulez-vous sauvegarder le modèle après l'entraînement ? "
            "(chemin ou 'non')"
        ),
        'visual': (
            "Voulez-vous activer l'affichage visuel ? (on/off)"
        ),
        'dontlearn': (
            "Voulez-vous désactiver l'apprentissage — mode test ? (oui/non)"
        ),
        'step_by_step': (
            "Voulez-vous avancer pas à pas (debug) ? (oui/non)"
        ),
    }

    def __init__(self):
        self.config = {
            'sessions': 1,
            'load_path': None,
            'save': None,
            'visual': 'off',
            'dontlearn': False,
            'step_by_step': False,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ask(self, question, default=None):
        """Pose une question et retourne la réponse de l'utilisateur."""
        suffix = f" [défaut: {default}]" if default is not None else ""
        try:
            answer = input(f"{question}{suffix}\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            return ''
        if answer:
            return answer
        return str(default) if default is not None else ''

    def _apply(self, topic, answer):
        """Applique la réponse de l'utilisateur à la configuration courante."""
        if topic == 'sessions':
            if answer.isdigit() and int(answer) > 0:
                self.config['sessions'] = int(answer)
        elif topic == 'load':
            if answer.lower() not in ('non', 'no', 'n', ''):
                self.config['load_path'] = answer
        elif topic == 'save':
            if answer.lower() not in ('non', 'no', 'n', ''):
                self.config['save'] = answer
        elif topic == 'visual':
            if answer in ('on', 'off'):
                self.config['visual'] = answer
        elif topic == 'dontlearn':
            if answer.lower() in ('oui', 'yes', 'o', 'y'):
                self.config['dontlearn'] = True
            elif answer.lower() in ('non', 'no', 'n'):
                self.config['dontlearn'] = False
        elif topic == 'step_by_step':
            if answer.lower() in ('oui', 'yes', 'o', 'y'):
                self.config['step_by_step'] = True
            elif answer.lower() in ('non', 'no', 'n'):
                self.config['step_by_step'] = False

    def _generate_followups(self, topic, answer):
        """Génère des questions de suivi selon le sujet et la réponse."""
        followups = []
        if topic == 'sessions':
            n = int(answer) if answer.isdigit() else 1
            if n >= 100:
                followups.append('save')
            followups.append('visual')
        elif topic == 'load':
            if answer.lower() not in ('non', 'no', 'n', ''):
                followups.append('dontlearn')
        elif topic == 'visual':
            if answer == 'on':
                followups.append('step_by_step')
        return followups

    def _show_config(self):
        """Affiche un résumé lisible de la configuration actuelle."""
        print("\n--- Configuration actuelle ---")
        print(f"  Sessions       : {self.config['sessions']}")
        print(f"  Modèle chargé  : {self.config['load_path'] or 'Aucun'}")
        print(f"  Sauvegarde     : {self.config['save'] or 'Aucune'}")
        print(f"  Affichage      : {self.config['visual']}")
        mode_test = 'Oui' if self.config['dontlearn'] else 'Non'
        pas_a_pas = 'Oui' if self.config['step_by_step'] else 'Non'
        print(f"  Mode test      : {mode_test}")
        print(f"  Pas à pas      : {pas_a_pas}")
        print("------------------------------\n")

    def _handle_remark(self, remark):
        """Analyse une remarque libre et génère des questions de suivi."""
        remark_lower = remark.lower()
        handled = False

        if any(w in remark_lower for w in
               ['session', 'train', 'entraîn', 'iter', 'nombre']):
            answer = self._ask(
                "Combien de sessions voulez-vous effectuer ?",
                default=self.config['sessions']
            )
            self._apply('sessions', answer)
            handled = True

        if any(w in remark_lower for w in
               ['modèle', 'model', 'load', 'charger', 'fichier']):
            answer = self._ask(
                "Chemin du modèle à charger (ou 'non') ?",
                default=self.config['load_path'] or 'non'
            )
            self._apply('load', answer)
            handled = True

        if any(w in remark_lower for w in
               ['sauvegarder', 'save', 'enregistrer', 'sauvegarde']):
            answer = self._ask(
                "Chemin de sauvegarde du modèle (ou 'non') ?",
                default=self.config['save'] or 'non'
            )
            self._apply('save', answer)
            handled = True

        if any(w in remark_lower for w in
               ['visual', 'affichage', 'voir', 'display', 'graphique']):
            answer = self._ask(
                "Activer l'affichage visuel ? (on/off)",
                default=self.config['visual']
            )
            self._apply('visual', answer)
            handled = True

        if any(w in remark_lower for w in
               ['apprendre', 'learn', 'test', 'évaluation', 'dontlearn']):
            answer = self._ask(
                "Désactiver l'apprentissage — mode test ? (oui/non)",
                default='oui' if self.config['dontlearn'] else 'non'
            )
            self._apply('dontlearn', answer)
            handled = True

        if not handled:
            print(
                "Remarque notée. Voici la configuration en cours :\n"
                "Vous pouvez mentionner : sessions, modèle, sauvegarde, "
                "affichage, apprentissage."
            )

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self):
        """Lance la session interactive et retourne la configuration finale."""
        print("\n=== Learn2Slither — Configuration interactive ===\n")

        queue = ['sessions', 'load']
        visited = set()

        while queue:
            topic = queue.pop(0)
            if topic in visited:
                continue
            visited.add(topic)

            answer = self._ask(self.QUESTIONS[topic])
            self._apply(topic, answer)

            for followup in self._generate_followups(topic, answer):
                if followup not in visited and followup not in queue:
                    queue.append(followup)

        self._show_config()

        while True:
            print(
                "Tapez 'finish' pour lancer l'entraînement,\n"
                "ou faites une remarque pour modifier la configuration."
            )
            user_input = input("> ").strip()

            if user_input.lower() == 'finish':
                break

            if user_input:
                self._handle_remark(user_input)
                self._show_config()

        print(
            "\nLancement de l'entraînement "
            "avec la configuration ci-dessus...\n"
        )
        return self.config


def run_ask_session():
    """Point d'entrée public du module ask."""
    session = AskSession()
    return session.run()
