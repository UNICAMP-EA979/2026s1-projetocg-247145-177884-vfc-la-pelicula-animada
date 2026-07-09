import numpy as np

from .node import Node


class Camera(Node):
    '''
    Camera node, a perspective camera
    '''

    def __init__(self, name: str = "camera") -> None:
        '''
        Camera initilizer

        Args:
            name (str, optional): node name. Defaults to "camera".
        '''
        super().__init__(name)

        self.near_plane = 1.0
        self.far_plane = 10.0
        self.screen_width = 1920.0
        self.screen_height = 1080.0
        self.vertical_fov = 60.0

    @property
    def projection_matrix(self) -> np.ndarray:
        '''
        Camera projection matrix

        Returns:
            np.ndarray: 4x4 projection matrix
        '''

        ## SEU CÓDIGO AQUI #####################################################
        # Crie a matriz de projeção perspectiva utilizando os parâmetros da câmera
        #aspect_ratio = self.screen_width / self.screen_height
        aspect_ratio = self.screen_width / self.screen_height
        fov_rad = np.radians(self.vertical_fov)
        f = 1.0 / np.tan(fov_rad / 2.0)
        
        near = self.near_plane
        far = self.far_plane
        
        matrix = np.array([
            [f / aspect_ratio, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
            [0, 0, -1, 0]
        ])
        #########################################################################
        
        return matrix
