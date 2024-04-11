#!/usr/bin/env python

from PIL import Image
import numpy as np
import sys


def charger_noyau(nom_fichier: str):
    """Chargement du noyau à partir du fichier texte de format :
        taille
        valeur_0_0 valeur_0_1 ... valeur_0_taille-1
        ...
        valeur_taille-1_0 ... valeur_taille-1_taille-1

    Retour:
    np.array(float): le noyau de convolution
    """

    with open(nom_fichier) as f:
        taille = int(f.readline().strip())

        assert 3 <= taille <= 255, \
            f'{nom_fichier} - taille de noyau invalide (<3 ou >255).'
        assert (taille % 2) == 1, \
            f'{nom_fichier} - taille de noyau invalide (mod 2 = 0).'

        noyau = np.loadtxt(f)

        assert noyau.shape == (taille, taille), \
            f'{nom_fichier} - il manque des valeurs dans le fichier.'

    return noyau


def prod_conv(image, filtre, val_min: int = 0, val_max: int = 255):
    """Produit de convolution - écrase l'image originale

    Arguments:
        image - numpy.ndarray, dtype=float64, matrice 3D
        filtre - numpy.ndarray, dtype=float64, matrice carrée
        val_min - tronquer les valeurs faibles à val_min (0 par défaut)
        val_max - tronquer les valeurs élevées à val_max (255 par défaut)

    Référence:
    https://fr.wikipedia.org/wiki/Produit_de_convolution
    """

    # Préparer le filtre pour le produit de convolution
    assert filtre.shape[0] == filtre.shape[1], "Le filtre n'est pas carré."
    filtre = filtre[::-1, ::-1].copy()

    # Calculer les marges autour de l'image
    taille_filtre = filtre.shape[0]
    marge = taille_filtre // 2  # Division entière
    marge_gauche = (marge + 15) & ~15  # Alignée sur 64o=16*4o

    print('Taille du filtre :', filtre.shape)
    print('  Strides (octets) :', filtre.strides)
    print('  Marge réelle : ', marge)
    print('  Marge alignée :', marge_gauche)

    # Créer une image temporaire avec les marges
    hauteur, largeur, canaux = image.shape
    stride = marge_gauche + ((largeur + marge + 15) & ~15)
    im_temp = np.ndarray(
        (marge + hauteur + marge, stride, canaux), dtype=image.dtype)

    print("Dimensions de l'image originale :", image.shape)
    print('  Strides (octets) :', image.strides)
    print(f'  Largeur totale alignée : {stride} (= {marge_gauche} +' +
        f' {largeur} + {stride - (marge_gauche + largeur)})')
    print('Dimensions modifiées :', im_temp.shape)
    print('  Strides (octets) :', im_temp.strides)

    # Remplir la marge du haut avec effet miroir vertical
    im_temp[marge - 1::-1, marge_gauche:marge_gauche + largeur, :] = \
        image[:marge, :, :]

    # Copier l'image originale en tenant compte des marges
    im_temp[marge:-marge, marge_gauche:marge_gauche + largeur, :] = image

    # Remplir la marge du bas avec effet miroir vertical
    im_temp[-1:-1 - marge:-1, marge_gauche:marge_gauche + largeur, :] = \
        image[-marge:, :, :]

    # Remplir les marges de gauche et de droite
    im_temp[:, marge_gauche - 1:marge_gauche - 1 - marge:-1, :] = \
        im_temp[:, marge_gauche:marge_gauche + marge, :]
    im_temp[:, marge_gauche + largeur:marge_gauche + largeur + marge, :] = \
        im_temp[:, marge_gauche+largeur-1:marge_gauche+largeur-1 - marge:-1, :]

    print('Filtrage en cours ...')

    # Prod_conv[i, j] = Sum(Im[i+marge ±marge, j+marge_gauche ±marge] * Filtre)
    for i in range(hauteur):
        for j in range(largeur):
            ii, jj = i + marge, j + marge_gauche
            for k in range(canaux):
                image[i, j, k] = np.vdot(
                    im_temp[ii-marge:ii+marge + 1, jj-marge:jj+marge + 1, k],
                    filtre)

    image.clip(val_min, val_max, out=image)


def main():
    """
    Programme principal
    """

    if len(sys.argv) < 3:
        sys.exit(f'Utilisation: {sys.argv[0]}' +
                 ' image.png fichier_noyau [resultat.png]')

    try:
        # Charger l'image originale en RGB
        image = np.array(Image.open(sys.argv[1]))[:, :, :3].astype(float)

        # Charger le noyau de convolution
        noyau = charger_noyau(sys.argv[2])
    except Exception as e:
        sys.exit(f'Erreur: {e}')

    # Calcul principal
    prod_conv(image, noyau)

    try:
        # Enregistrer l'image résultante
        Image.fromarray(image.astype(np.uint8), 'RGB').save("resultat.png")
    except Exception as e:
        sys.exit(f'Erreur: {e}')


if __name__ == '__main__':
    main()
