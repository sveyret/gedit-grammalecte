# gedit-grammalecte

gedit-grammalecte est un greffon permettant l'intégration du correcteur grammatical _Grammalecte_ dans l'éditeur _gedit_.

# Language/langue

:us: :gb:

Grammalecte is a French language grammar checker. Therefore, it is supposed that anyone interrested by this project has at least basic knowledge of French. That's why all documentation is in French only.

Anyway, because English is the language of programming, the code, including variable names and comments, are in English.

:fr:

Grammalecte est un correcteur grammatical pour la langue française. Aussi, on suppose que toute personne intéressée par ce projet a au moins une connaissance basique du français. C'est pourquoi toute la documentation est uniquement en français.

Toutefois, l'anglais étant la langue de la programmation, le code source, incluant les noms de variables et les commentaires, sont en anglais.

# Licence

Copyright © 2021 Stéphane Veyret stephane_AT_neptura_DOT_org

:us: :gb:

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.

:fr:

Ce programme est un logiciel libre ; vous pouvez le redistribuer ou le modifier suivant les termes de la GNU General Public License telle que publiée par la Free Software Foundation ; soit la version 3 de la licence, soit (à votre gré) toute version ultérieure.

Ce programme est distribué dans l'espoir qu'il sera utile, mais SANS AUCUNE GARANTIE ; sans même la garantie tacite de QUALITÉ MARCHANDE ou d'ADÉQUATION à UN BUT PARTICULIER. Consultez la GNU General Public License pour plus de détails.

Vous devez avoir reçu une copie de la GNU General Public License en même temps que ce programme ; si ce n'est pas le cas, consultez http://www.gnu.org/licenses.

# Aperçu

![Infobulle](https://user-images.githubusercontent.com/6187210/32458521-fd71a990-c32c-11e7-8b2b-43764d608480.png)

# Pré-requis

Pour utiliser ce greffon, vous devez avoir :
* le module [Grammalecte](http://grammalecte.net/) téléchargé et installé sur la machine ;
* une version de _gedit_ capable d'exécuter les greffons Python (cela peut nécessiter une compilation particulière) ;
* et, bien sûr, Python 3 (3.3 minimum) nécessaires au fonctionnement de ces deux pré-requis.

# Installation

Téléchargez la version désirée sur [la page des _releases_](https://github.com/sveyret/gedit-grammalecte/releases), au format _zip_ ou _tar.gz_, puis décompressez-la dans le répertoire de votre choix.

La compilation et l'installation du greffon se fait à l'aide des commandes :

    make && make install

Par défaut, l'installation se fera pour tout le système, et nécessite donc les droits d'administration sur la machine. Si vous souhaitez une installation différente, vous pouvez utiliser les variables :
* `DESTDIR` pour faire une installation dans un répertoire différent, généralement utilisé en phase de _stage_ avant une installation réelle,
* `LOCALE_INSTALL` pour indiquer le répertoire d'installation des traductions,
* `PLUGIN_INSTALL` pour indiquer le répertoire d'installation du greffon.

Pour une installation en local, vous pouvez, par exemple, exécuter la commande :

    make && make LOCALE_INSTALL=$HOME/.local/share/locale PLUGIN_INSTALL=$HOME/.local/share install

Dans ce dernier cas, il vous faudra modifier la configuration du greffon en éditant (ou créant, si nécessaire) le fichier `$HOME/.config/gedit/grammalecte.conf`. Ce fichier est au format JSON. Le répertoire d’installation des traductions doit être indiqué dans la clé `locale-dir`.

Exemple :

    > cat ~/.config/gedit/grammalecte.conf
    { "locale-dir": "/home/user/.local/share/locale" }

# Utilisation

## Vérification automatique

Lorsque la vérification automatique est activée, le greffon souligne en temps réel les erreurs d'orthographe ou grammaire dans _gedit_. Lorsque le curseur de la souris survole une erreur, une bulle d'information est affiché pour expliquer le problème détecté. Pour activer ou désactiver la vérification automatique, utilisez l'option « Vérification linguistique automatique » dans le menu « Outils ». Par défaut, l'option est désactivée, mais si vous l'activez pour un fichier donné, elle le restera pour ce fichier, même après sa fermeture.

## Menu contextuel

Lorsque le curseur est sur une erreur, l'éventuel menu contextuel est enrichi d'un nouveau sous-menu « Suggestions ». Ce sous-menu contient les options suivantes :
* la liste des suggestions liées à l'erreur, afin de remplacer l'erreur par une proposition ;
* `Ignorer la règle` qui permet de signaler à Grammalecte de ne plus afficher d'erreur par rapport à cette règle de grammaire dans le document en cours ;
* `Ignorer l'erreur` pour que cette erreur ne soit plus signalée dans le document en cours (si un même contexte d'erreur est trouvé plusieurs fois dans le fichier, il sera ignoré à chaque fois — le contexte d'erreur correspond à ce qui est affiché dans l'info-bulle lorsque le curseur survole l'erreur) ;
* `Ajouter` permet d'ajouter l'erreur dans le dictionnaire personnel afin qu'elle ne soit plus détectée quel que soit le document (l'action est en fait la même que pour `Ignorer l'erreur` mais la configuration est enregistrée dans la configuration de l'utilisateur et non dans les métadonnées du fichier) ;
* `Voir la règle` ouvre une page Internet si un lien est fourni avec la règle de grammaire.

## Configurer

Pour sélectionner les options utilisées avec Grammalecte avec un fichier particulier, vous pouvez, lorsque ce fichier est chargé dans la fenêtre principale, aller dans le menu « Outils » et choisir l'option « Configurer Grammalecte... ». Une fenêtre présente alors les options disponibles que vous pouvez cocher ou non. Vos choix seront enregistrés dans les métadonnées du fichier. Il est possible de supprimer toute la configuration (options spécifiques, règles ou erreurs ignorées, etc.) d'un fichier depuis cette boite de dialogue à l'aide du bouton « Effacer ».

Pour une configuration globale, valable pour tous les fichiers, il faut sélectionner le greffon dans le menu adéquat de _gedit_ et cliquer sur « Préférences ». Les préférences globales seront enregistrées dans votre configuration utilisateur.

# Configuration

La configuration de Grammalecte est écrite dans des fichiers JSON. Ces fichiers se trouvent :
* pour la configuration globale au système, dans `/etc/gedit/grammalecte.conf` ;
* pour la configuration spécifique à l'utilisateur, dans `$HOME/.config/gedit/grammalecte.conf` ;
* pour la configuration spécifique à un fichier, dans les métadonnées du fichier.

Chaque fichier de configuration peut surcharger les valeurs présentes dans le fichier plus global. À contrario, une valeur non définie dans le fichier plus précis sera recherchée dans le fichier plus global.

Les paramètres configurables sont les suivants :
* `locale-dir` contient le chemin vers le répertoire des traductions ;
* `analyze-options` contient les options d'analyse et leurs valeurs ;
* `auto-analyze-active` indique si la vérification automatique est activée ou non ;
* `analyze-parallel-count`<sup>1</sup> indique le nombre d’analyze pouvant être lancées en parallèle ;
* `analyze-wait-ticks`<sup>1</sup> contient la durée de carence (en dixièmes de seconde) sans évènement avant de lancer l'analyse automatique ;
* `ign-rules`<sup>2</sup> contient les règles qui sont ignorés par Grammalecte ;
* `ign-errors`<sup>2</sup> contient les erreurs (orthographe ou grammaire) qui doivent être ignorés ;
* `concat-lines` indique que les lignes doivent être concaténées pour former un paragraphe (il faut alors une ligne vide entre les paragraphes).

[1] Ces options sont pour les utilisateurs avertis uniquement, à ne modifier que si vous savez ce que vous faites !

[2] Ces options se cumulent au niveau des différents fichiers, c'est-à-dire que les tableaux définis à un niveau du dessus sont complétés et non remplacés par ceux du niveau inférieur.

# À faire

- [ ] Ajouter un moyen d'éditer le « dictionnaire personnel ».
- [ ] Améliorer la configuration interactive (par exemple, pouvoir modifier CONCAT_LINES).
- [ ] Ajouter une correction interactive.
- [ ] Optimiser la correction (effectuer la correction par paragraphe).
