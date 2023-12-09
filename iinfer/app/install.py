from iinfer.app import common
from importlib.resources import files
from pathlib import Path
import logging
import platform
import shutil

class Install(object):
    def __init__(self, logger: logging.Logger, wsl_name: str = None, wsl_user: str = None):
        self.logger = logger
        self.wsl_name = wsl_name
        self.wsl_user = wsl_user

    def redis(self):
        cmd = f"docker pull ubuntu/redis:latest"
        if platform.system() == 'Windows':
            if self.wsl_name is None:
                return {"warn":f"wsl_name option is required."}
            if self.wsl_user is None:
                return {"warn":f"wsl_user option is required."}
            returncode, _ = common.cmd(f"wsl -d {self.wsl_name} -u {self.wsl_user} {cmd}", self.logger)
            if returncode != 0:
                common.print_format({"warn":f"Failed to install redis-server."}, format, tm)
                self.logger.error(f"Failed to install redis-server.")
                return {"error": f"Failed to install redis-server."}
            return {"success": f"Success to install redis-server."}

        elif platform.system() == 'Linux':
            returncode, _ = common.cmd(f"{cmd}", self.logger)
            if returncode != 0:
                common.print_format({"warn":f"Failed to install redis-server."}, format, tm)
                self.logger.error(f"Failed to install redis-server.")
                return {"error": f"Failed to install redis-server."}
            return {"success": f"Success to install redis-server."}

        else:
            return {"warn":f"Unsupported platform."}

    def server(self):
        from iinfer import version
        dockerfile = files(common.APP_ID).joinpath("docker/Dockerfile")
        dockercompose = files(common.APP_ID).joinpath("docker/docker-compose.yml")
        cmd = f"docker build -t hamacom/iinfer:{version.__version__} --build-arg VERSION=${version.__version__} -f {dockerfile} ."
        if platform.system() == 'Windows':
            return {"warn": f"Build server command is Unsupported in windows platform."}

        elif platform.system() == 'Linux':
            returncode, _ = common.cmd(f"{cmd}", self.logger)
            if returncode != 0:
                common.print_format({"warn":f"Failed to install iinfer-server."}, format, tm)
                self.logger.error(f"Failed to install iinfer-server.")
                return {"error": f"Failed to install iinfer-server."}
            shutil.copy(dockercompose, './')
            return {"success": f"Success to install iinfer-server. and docker-compose.yml is copied."}

        else:
            return {"warn":f"Unsupported platform."}

    def onnx(self):
        returncode, _ = common.cmd('pip install onnxruntime', logger=self.logger)
        if returncode != 0:
            common.print_format({"warn":f"Failed to install onnxruntime."}, format, tm)
            self.logger.error(f"Failed to install onnxruntime.")
            return {"error": f"Failed to install onnxruntime."}
        return {"success": f"Success to install onnxruntime."}

    def mmdet(self, data_dir: Path):
        returncode, _ = common.cmd(f'git clone https://github.com/open-mmlab/mmdetection.git', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to git clone mmdetection.")
            return {"error": f"Failed to git clone mmdetection."}
        srcdir = Path('.') / 'mmdetection'
        shutil.copytree(srcdir, data_dir / 'mmdetection', dirs_exist_ok=True)
        shutil.rmtree(srcdir, ignore_errors=True)

        returncode, _ = common.cmd('pip install torch torchvision openmim', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install torch.")
            return {"error": f"Failed to install torch."}

        returncode, _ = common.cmd('mim install mmengine mmcv mmdet', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install mmdet.")
            return {"error": f"Failed to install mmdet."}

        if srcdir.exists():
            return {"success": f"Please remove '{srcdir / 'mmdetection'}' manually."}
        return {"success": f"Success to install mmdet."}

    def mmcls(self):
        returncode, _ = common.cmd('pip install torch torchvision openmim', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install torch.")
            return {"error": f"Failed to install torch."}

        returncode, _ = common.cmd('mim install mmengine mmcv mmcls', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install mmcls.")
            return {"error": f"Failed to install mmcls."}

        return {"success": f"Success to install mmcls."}

    def mmpretrain(self, data_dir: Path):
        returncode, _ = common.cmd(f'git clone https://github.com/open-mmlab/mmpretrain.git', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to git clone mmpretrain.")
            return {"error": f"Failed to git clone mmpretrain."}
        srcdir = Path('.') / 'mmpretrain'
        shutil.copytree(srcdir, data_dir / 'mmpretrain', dirs_exist_ok=True)
        shutil.rmtree(srcdir, ignore_errors=True)

        returncode, _ = common.cmd('pip install torch torchvision openmim', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install torch.")
            return {"error": f"Failed to install torch."}

        returncode, _ = common.cmd('pip uninstall -y mmcv', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to uninstall mmcv.")
            return {"error": f"Failed to uninstall mmcv."}

        returncode, _ = common.cmd('mim install mmengine mmcv>=2.0.0 mmpretrain', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install mmpretrain.")
            return {"error": f"Failed to install mmpretrain."}

        if srcdir.exists():
            return {"success": f"Please remove '{srcdir}' manually."}
        return {"success": f"Success to install mmpretrain."}
