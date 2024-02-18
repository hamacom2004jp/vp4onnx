from iinfer import version
from iinfer.app import common
from pathlib import Path
import getpass
import logging
import os
import platform
import shutil
import yaml

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
                self.logger.error(f"Failed to install redis-server.")
                return {"error": f"Failed to install redis-server."}
            return {"success": f"Success to install redis-server."}

        elif platform.system() == 'Linux':
            returncode, _ = common.cmd(f"{cmd}", self.logger)
            if returncode != 0:
                self.logger.error(f"Failed to install redis-server.")
                return {"error": f"Failed to install redis-server."}
            return {"success": f"Success to install redis-server."}

        else:
            return {"warn":f"Unsupported platform."}

    def server(self, data:Path, install_iinfer:str='iinfer', install_onnx:bool=True,
               install_mmdet:bool=True, install_mmcls:bool=False, install_mmpretrain:bool=True, install_mmrotate:bool=False, install_use_gpu:bool=False,
               install_insightface=False, install_tag:str=None):
        if platform.system() == 'Windows':
            return {"warn": f"Build server command is Unsupported in windows platform."}
        from importlib.resources import read_text
        user = getpass.getuser()
        install_tag = f"_{install_tag}" if install_tag is not None else ''
        with open('Dockerfile', 'w', encoding='utf-8') as fp:
            text = read_text(f'{common.APP_ID}.docker', 'Dockerfile')
            wheel = Path(install_iinfer)
            if wheel.exists() and wheel.suffix == '.whl':
                shutil.copy(wheel, Path('.').resolve() / wheel.name)
                install_iinfer = f'/home/{user}/{wheel.name}'
                text = text.replace('#{COPY_IINFER}', f'COPY {wheel.name} {install_iinfer}')
            else:
                text = text.replace('#{COPY_IINFER}', '')
            text = text.replace('${MKUSER}', user)
            text = text.replace('#{INSTALL_TAG}', install_tag)
            text = text.replace('#{INSTALL_IINFER}', install_iinfer)
            text = text.replace('#{INSTALL_ONNX}', f'RUN iinfer -m install -c onnx --data /home/{user}/.iinfer' if install_onnx else '')
            text = text.replace('#{INSTALL_MMDET}', f'RUN iinfer -m install -c mmdet --data /home/{user}/.iinfer' if install_mmdet else '')
            text = text.replace('#{INSTALL_MMCLS}', f'RUN iinfer -m install -c mmcls --data /home/{user}/.iinfer' if install_mmcls else '')
            text = text.replace('#{INSTALL_MMPRETRAIN}', f'RUN iinfer -m install -c mmpretrain --data /home/{user}/.iinfer' if install_mmpretrain else '')
            text = text.replace('#{INSTALL_MMROTATE}', f'RUN iinfer -m install -c mmrotate --data /home/{user}/.iinfer' if install_mmrotate else '')
            text = text.replace('#{INSTALL_INSIGHTFACE}', f'RUN iinfer -m install -c insightface --data /home/{user}/.iinfer' if install_insightface else '')
            fp.write(text)
        docker_compose_path = Path('docker-compose.yml')
        if not docker_compose_path.exists():
            with open(docker_compose_path, 'w', encoding='utf-8') as fp:
                text = read_text(f'{common.APP_ID}.docker', 'docker-compose.yml')
                fp.write(text)
        with open(f'docker-compose.yml', 'r+', encoding='utf-8') as fp:
            comp = yaml.safe_load(fp)
            services = comp['services']
            common.mkdirs(data)
            services[f'iinfer_server{install_tag}'] = dict(
                image=f'hamacom/iinfer:{version.__version__}{install_tag}',
                container_name=f'iinfer_server{install_tag}',
                environment=dict(
                    TZ='Asia/Tokyo',
                    REDIS_HOST='${REDIS_HOST:-redis}',
                    REDIS_PORT='${REDIS_PORT:-6379}',
                    REDIS_PASSWORD='${REDIS_PASSWORD:-password}',
                    SVNAME='${SVNAME:-server'+install_tag+'}'
                ),
                networks=['backend'],
                user=user,
                restart='always',
                working_dir=f'/home/{user}',
                volumes=[
                    f'~/:/home/{user}/',
                    f'{data}:/home/{user}/.iinfer'
                ]
            )
            fp.seek(0)
            yaml.dump(comp, fp)
        cmd = f'docker build -t hamacom/iinfer:{version.__version__}{install_tag} -f Dockerfile .'

        if platform.system() == 'Linux':
            returncode, _ = common.cmd(f"{cmd}", self.logger, True)
            os.remove('Dockerfile')
            if returncode != 0:
                self.logger.error(f"Failed to install iinfer-server.")
                return {"error": f"Failed to install iinfer-server."}
            return {"success": f"Success to install iinfer-server. and docker-compose.yml is copied."}

        else:
            return {"warn":f"Unsupported platform."}

    def onnx(self):
        returncode, _ = common.cmd('pip install onnxruntime', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install onnxruntime.")
            return {"error": f"Failed to install onnxruntime."}
        return {"success": f"Success to install onnxruntime."}

    def insightface(self, data_dir: Path):
        returncode, _ = common.cmd('pip install cython', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install cython.")
            return {"error": f"Failed to install cython."}
        returncode, _ = common.cmd('pip install onnxruntime', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install onnxruntime.")
            return {"error": f"Failed to install onnxruntime."}
        returncode, _ = common.cmd('python -m pip install --upgrade pip setuptools', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install setuptools.")
            return {"error": f"Failed to install setuptools."}
        returncode, _ = common.cmd('pip install insightface', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install insightface.")
            return {"error": f"Failed to install insightface."}
        return {"success": f"Success to install insightface."}

    def _torch(self, install_use_gpu:bool=False):
        if install_use_gpu:
            returncode, _ = common.cmd('pip install torch==2.1.0 torchvision --index-url https://download.pytorch.org/whl/cu118', logger=self.logger)
        else:
            returncode, _ = common.cmd('pip install torch==2.1.0 torchvision', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install torch.")
            return {"error": f"Failed to install torch."}
        return {"success": f"Success to install torch."}

    def _openmin(self, install_use_gpu:bool=False):
        returncode, _ = common.cmd('pip install openmim', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install openmim.")
            return {"error": f"Failed to install openmim."}
        return {"success": f"Success to install openmim."}

    def _mmcv(self, install_use_gpu:bool=False):
        if install_use_gpu:
            returncode, _ = common.cmd('pip install mmcv==2.1.0 -f https://download.openmmlab.com/mmcv/dist/cu118/torch2.1/index.html', logger=self.logger)
            if returncode != 0:
                self.logger.error(f"Failed to install mmcv.")
                return {"error": f"Failed to install mmcv."}
        else:
            returncode, _ = common.cmd('mim install mmcv>=2.0.0', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to install mmcv.")
            return {"error": f"Failed to install mmcv."}
        return {"success": f"Success to install mmcv."}

    def mmdet(self, data_dir:Path, install_use_gpu:bool=False):
        returncode, _ = common.cmd(f'git clone https://github.com/open-mmlab/mmdetection.git', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to git clone mmdetection.")
            return {"error": f"Failed to git clone mmdetection."}
        srcdir = Path('.') / 'mmdetection'
        shutil.copytree(srcdir, data_dir / 'mmdetection', dirs_exist_ok=True, ignore=shutil.ignore_patterns('.git'))
        shutil.rmtree(srcdir, ignore_errors=True)

        ret = self._torch(install_use_gpu)
        if "error" in ret: return ret
        ret = self._openmin(install_use_gpu)
        if "error" in ret: return ret
        ret = self._mmcv(install_use_gpu)
        if "error" in ret: return ret

        ret, _ = common.cmd('mim install mmengine mmdet', logger=self.logger)
        if ret != 0:
            self.logger.error(f"Failed to install mmengine mmdet.")
            return {"error": f"Failed to install mmengine mmdet."}

        if srcdir.exists():
            return {"success": f"Please remove '{srcdir / 'mmdetection'}' manually."}
        return {"success": f"Success to install mmdet."}

    def mmrotate(self, data_dir:Path, install_use_gpu:bool=False):
        returncode, _ = common.cmd(f'git clone https://github.com/open-mmlab/mmrotate.git', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to git clone mmrotate.")
            return {"error": f"Failed to git clone mmrotate."}
        srcdir = Path('.') / 'mmrotate'
        shutil.copytree(srcdir, data_dir / 'mmrotate', dirs_exist_ok=True, ignore=shutil.ignore_patterns('.git'))
        shutil.rmtree(srcdir, ignore_errors=True)

        ret = self._torch(install_use_gpu)
        if "error" in ret: return ret
        ret = self._openmin(install_use_gpu)
        if "error" in ret: return ret
        ret = self._mmcv(install_use_gpu)
        if "error" in ret: return ret

        ret, _ = common.cmd('mim install mmengine mmdet mmrotate', logger=self.logger)
        if ret != 0:
            self.logger.error(f"Failed to install mmengine mmdet mmrotate.")
            return {"error": f"Failed to install mmengine mmdet mmrotate."}

        if srcdir.exists():
            return {"success": f"Please remove '{srcdir / 'mmrotate'}' manually."}
        return {"success": f"Success to install mmrotate."}

    def mmcls(self, data_dir:Path, install_use_gpu:bool=False):

        ret = self._torch(install_use_gpu)
        if "error" in ret: return ret
        ret = self._openmin(install_use_gpu)
        if "error" in ret: return ret
        ret = self._mmcv(install_use_gpu)
        if "error" in ret: return ret

        ret, _ = common.cmd('mim install mmengine mmcls', logger=self.logger)
        if ret != 0:
            self.logger.error(f"Failed to install mmengine mmcls.")
            return {"error": f"Failed to install mmengine mmcls."}

        return {"success": f"Success to install mmcls."}

    def mmpretrain(self, data_dir:Path, install_use_gpu:bool=False):
        returncode, _ = common.cmd(f'git clone https://github.com/open-mmlab/mmpretrain.git', logger=self.logger)
        if returncode != 0:
            self.logger.error(f"Failed to git clone mmpretrain.")
            return {"error": f"Failed to git clone mmpretrain."}
        srcdir = Path('.') / 'mmpretrain'
        shutil.copytree(srcdir, data_dir / 'mmpretrain', dirs_exist_ok=True, ignore=shutil.ignore_patterns('.git'))
        shutil.rmtree(srcdir, ignore_errors=True)

        ret = self._torch(install_use_gpu)
        if "error" in ret: return ret
        ret = self._openmin(install_use_gpu)
        if "error" in ret: return ret
        ret = self._mmcv(install_use_gpu)
        if "error" in ret: return ret

        ret, _ = common.cmd('mim install mmengine mmpretrain', logger=self.logger)
        if ret != 0:
            self.logger.error(f"Failed to install mmpretrain.")
            return {"error": f"Failed to install mmpretrain."}

        if srcdir.exists():
            return {"success": f"Please remove '{srcdir}' manually."}
        return {"success": f"Success to install mmpretrain."}
