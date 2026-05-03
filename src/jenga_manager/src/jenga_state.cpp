#include "jenga_manager/jenga_state.hpp"
#include <cmath>
#include <algorithm> // Pour std::min_element ou std::find

/**
 * AJOUTER UN JENGA
 * Syntaxe : Insertion dans une std::map
 */
void WorldState::addJenga(std::shared_ptr<Jenga> jenga) {
    this->all_jengas_[jenga->id] = jenga;
    // Si un callback est enregistré, on l'exécute
    if (on_add_jenga_) {
        on_add_jenga_(jenga);
    }
}

void WorldState::removeJenga(std::string id) {
    auto it = all_jengas_.find(id);
    if (it != all_jengas_.end()) {
        std::string uuid_to_remove_global = it->second->uuid_global;
        std::string uuid_to_remove_local = it->second->uuid_local;
        this->all_jengas_.erase(it);

        // Si le jenga avait un UUID Nav2 et qu'on a un callback
        if (!uuid_to_remove_global.empty() && on_remove_jenga_) {
            on_remove_jenga_(uuid_to_remove_global);
        }
        if (!uuid_to_remove_local.empty() && on_remove_jenga_) {
            on_remove_jenga_(uuid_to_remove_local);
        }
    }
}

void WorldState::clearAllJengas() {
    this->all_jengas_.clear();
    if (on_clear_all_jengas_) {
        on_clear_all_jengas_();
    }
}

/**
 * AJOUTER UN GROUPE
 * Syntaxe : Itération sur un vecteur de pointeurs
 */
void WorldState::addGroup(std::shared_ptr<JengaGroup> group) {
    // Parcourir les membres du groupe
    // group->members est un std::vector<std::shared_ptr<Jenga>>
    for (auto const& j : group->members) {
        // Appeler ta propre fonction addJenga pour chaque élément
        this->addJenga(j);
    }
}

/**
 * TROUVER LE PLUS PROCHE
 * Syntaxe : Itération sur une Map et calcul de distance
 */
std::shared_ptr<Jenga> WorldState::findNearest(double x, double y) {
    if (this->all_jengas_.empty()) return nullptr;
    std::shared_ptr<Jenga> nearest = nullptr;
    double min_dist = std::numeric_limits<double>::max();

    // Itération sur une map (paire clé/valeur)
    // entry.first  -> la string (ID)
    // entry.second -> le shared_ptr<Jenga>
    for (auto const& [id, jenga_ptr] : this->all_jengas_) {
        double dist = std::hypot(x - jenga_ptr->x, y - jenga_ptr->y);
        if (dist < min_dist) {
                min_dist = dist;
                nearest = jenga_ptr;
        }
        // Calcule la distance ici : sqrt(pow(x2-x1, 2) + pow(y2-y1, 2))
        // Compare avec min_dist et met à jour 'nearest'
    }

    return nearest;
}

/**
 * EXISTENCE D'UN JENGA
 */
bool WorldState::exist(std::string id) {
    return this->all_jengas_.count(id);
}

/**
 * RÉCUPÉRER INFOS
 */
std::shared_ptr<Jenga> WorldState::getJenga(std::string id) {
    // find() renvoie un itérateur. S'il vaut end(), c'est que rien n'a été trouvé.
    auto it = this->all_jengas_.find(id);
    if (it != this->all_jengas_.end()) {
        return it->second;
    }
    return nullptr;
}

