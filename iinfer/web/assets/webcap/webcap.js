const change_dark_mode = (dark_mode) => {
  const html = $('html');
  if(dark_mode) html.attr('data-bs-theme','dark');
  else if(html.attr('data-bs-theme')=='dark') html.removeAttr('data-bs-theme');
  else html.attr('data-bs-theme','dark');
}
const show_loading = () => {
  const loading = $('#loading');
  loading.removeClass('d-none');
}
const hide_loading = () => {
  const loading = $('#loading');
  loading.addClass('d-none');
  const progress = $('#progress');
  progress.addClass('d-none');
}
const webcap = {}
webcap.message = (res) => {
  msg = JSON.stringify(res)
  alert(msg.replace(/\\n/g, '\n'));
  hide_loading();
}
/** 初期化処理 */
webcap.init = () => {
  /** webcapが可能なpipelineの読込み */
  list_pipe(null).then(async (result) => {
    const pipeline_elem = $('#pipeline');
    for (const pipe of result) {
      if (!pipe || pipe.pipe_cmd.length == 0) continue;
      // pipe_cmdの最初の要素にwebcapコマンドがあるか確認
      const webcap_cmd = await load_cmd(pipe.pipe_cmd[0]);
      const outputs_key_str = webcap_cmd.outputs_key ? webcap_cmd.outputs_key.join(',') : "";
      if (!webcap_cmd || webcap_cmd.mode != 'web' || webcap_cmd.cmd != 'webcap') continue;
      url = `webcap/pub_img/${webcap_cmd.listen_port}`
      if (webcap_cmd.access_url) url = webcap_cmd.access_url;
      // pipe_cmdの最後の要素にshowimgコマンドがあるか確認
      const showimg_cmd = await load_cmd(pipe.pipe_cmd[pipe.pipe_cmd.length - 1]);
      if (!showimg_cmd || showimg_cmd.mode != 'postprocess' || showimg_cmd.cmd != 'showimg') continue;
      const elem = $(`<li class="dropdown-submenu"><span class="ps-2 ${pipe.title}"/><a class="d-inline ps-2 dropdown-item" href="#" onclick="webcap.change_pipeline('${pipe.title}', '${url}', '${outputs_key_str}');">${pipe.title}</a></li>`);
      pipeline_elem.append(elem);
      webcap.change_pipeline(pipe.title, url, outputs_key_str);
    }
    if (pipeline_elem.find('.dropdown-submenu').length <= 0) {
      const elem = $(`<li class="dropdown-submenu"><a class="dropdown-item" href="#">&lt; Not found webcap to showimg pipeline &gt;</a></li>`);
      pipeline_elem.append(elem);
      webcap.change_pipeline(null, null, "");
    }
    hide_loading();
  });
  $('#rec_error').off('click').on('click', () => {
    webcap.message('Please select pipeline and Camera.');
  });
  /** 使用可能なカメラ一覧の読込み */
  const camera_selection = async () => {
    if (!('mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices)) {
      webcap.message('No camera found.');
      return;
    }
    try {
      await navigator.mediaDevices.getUserMedia({video: true});
    }
    catch (e) {
      webcap.message('No camera found.');
      return;
    }
    const devices = await navigator.mediaDevices.enumerateDevices();
    const videoDevices = devices.filter(device => device.kind === 'videoinput');
    const camera_elem = $('#camera');
    webcap.camera = {};
    videoDevices.map(videoDevice => {
      if (!videoDevice.deviceId) return;
      const elem = $(`<li class="dropdown-submenu"><span class="ps-2 ${videoDevice.deviceId}"/><a class="d-inline ps-2 dropdown-item" href="#" onclick="webcap.change_camera('${videoDevice.deviceId}', '${videoDevice.label}');">${videoDevice.label}</a></li>`);
      camera_elem.append(elem);
    });
    camera_elem.find('.dropdown-submenu .dropdown-item:first').click();
  };
  camera_selection();
  /** イベントハンドラの設定 */
  webcap.container_elem = $('#img_container');
  webcap.video_elem = $('#video');
  webcap.video = webcap.video_elem.get(0);
  webcap.buffer_elem = $('#buffer');
  webcap.buffer = webcap.buffer_elem.get(0);
  webcap.buffer_2d = webcap.buffer.getContext('2d')
  webcap.canvas_elem = $('#canvas');
  webcap.canvas = webcap.canvas_elem.get(0);
  webcap.canvas_2d = webcap.canvas.getContext('2d')
  $('#rec').off('click').on('click', webcap.rec_start);
  $('#pause').off('click').on('click', webcap.rec_stop);
  $(window).resize(async () => {
    await webcap.resize();
  });
  webcap.video_elem.on('play', webcap.rec);
};
/** カメラの設定をpipelineのwebcapコマンドから取得 */
webcap.get_camera_const = async (title) => {
  if (!webcap.camera) webcap.camera = {};
  if (!title) {
    webcap.camera.cmd = {};
    webcap.camera.capture_fps = 10;
    return {
      video: {
        width: 640,
        height: 480
      },
      audio: false,
    };
  }
  const pipe = await load_pipe(title);
  const cmd = await load_cmd(pipe.pipe_cmd[0]);
  webcap.camera.cmd = cmd;
  const constraints = {
    video: {
      deviceId: {
        exact: webcap.camera.deviceId
      },
      width: cmd.capture_frame_width,
      height: cmd.capture_frame_height
    },
    audio: false,
  };
  return constraints;
};
/** カメラの切り替え */
webcap.change_camera = (deviceId, label) => {
  webcap.video.pause();
  webcap.video.srcObject = null
  webcap.camera.deviceId = deviceId;
  webcap.camera.label = label;
  const camera_elem = $('#camera');
  camera_elem.find('.dropdown-submenu span').html("&nbsp;");
  camera_elem.find(`.${deviceId}`).text("*");
  webcap.stream();
};
/** カメラ映像取得 */
webcap.stream = async () => {
  const constraints = await webcap.resize();
  webcap.video.srcObject = await navigator.mediaDevices.getUserMedia(constraints);
  const track = webcap.video.srcObject.getVideoTracks()[0];
  webcap.video_settings = track.getSettings();
  webcap.video.play();
};
/** windowサイズ変更ハンドラ */
webcap.resize = async () => {
  let constraints = {};
  if (webcap.pipeline && webcap.pipeline.title) {
    constraints = await webcap.get_camera_const(webcap.pipeline.title);
  } else {
    constraints = await webcap.get_camera_const(null);
  }
  const width = parseInt(webcap.container_elem.width() - 10);
  const height = parseInt(webcap.container_elem.height() - 10);
  webcap.video_elem.attr('height', height).attr('width', width);
  webcap.buffer_elem.attr('height', height).attr('width', width);
  webcap.canvas_elem.attr('height', height).attr('width', width);
  return constraints;
};
/** pipelineの切り替え */
webcap.change_pipeline = (title, url, outputs_key_str) => {
  if (!webcap.pipeline) webcap.pipeline = {};
  webcap.pipeline.title = title;
  webcap.pipeline.url = url;
  webcap.pipeline.is_rec = false;
  webcap.pipeline.outputs_key_str = outputs_key_str;
  webcap.get_camera_const(title)
  if (!title) {
    $('#rec').hide();
    $('#pause').hide();
    $('#rec_error').show();
    $('#navi_title').text(`WebCap`);
    return;
  }
  $('#pause').hide();
  $('#rec_error').hide();
  $('#navi_title').text(`WebCap ( ${title} )`);
  const pipeline_elem = $('#pipeline');
  pipeline_elem.find('.dropdown-submenu span').text("&nbsp;");
  pipeline_elem.find(`.${title}`).text("*");
  fetch(webcap.pipeline.url, {method: "GET", mode:'cors'});
};
/** カメラ映像をwebcapに送信開始 */
webcap.rec_start = () => {
  if (!webcap.pipeline || webcap.pipeline.length <= 0) {
    webcap.message('Please select pipeline.');
    return;
  }
  if (webcap.pipeline.is_rec) return;
  $('#rec').hide();
  $('#pause').show();
  webcap.pipeline.is_rec = true;
  show_loading();
};
/** カメラ映像をwebcapに送信停止 */
webcap.rec_stop = () => {
  $('#rec').show();
  $('#pause').hide();
  hide_loading();
  webcap.pipeline.is_rec = false;
};
/** アスペクト比計算 */
webcap.calc_aspect = (video_width, video_height, canvas_width, canvas_height) => {
  const videoAspectRatio = video_width / video_height;
  const canvasAspectRatio = canvas_width / canvas_height;
  let renderableHeight, renderableWidth, xStart, yStart;
  const padding = 10;
  if(videoAspectRatio < canvasAspectRatio) {
    renderableHeight = canvas_height - padding;
    renderableWidth = videoAspectRatio * renderableHeight - padding;
    xStart = (canvas_width - renderableWidth) / 2;
    yStart = 0;
  } else {
    renderableWidth = canvas_width - padding;
    renderableHeight = renderableWidth / videoAspectRatio - padding;
    xStart = 0;
    yStart = (canvas_height - renderableHeight) / 2;
  }
  return [xStart, yStart, renderableWidth, renderableHeight];
};
/** カメラ映像をwebcapに送信 */
webcap.rec = () => {
  if (!webcap.video.srcObject) {
    return;
  }
  const aspect = webcap.calc_aspect(webcap.video_settings.width, webcap.video_settings.height, webcap.canvas.width, webcap.canvas.height);
  // バッファにvideoの内容を描画
  webcap.buffer_2d.drawImage(webcap.video, aspect[0], aspect[1], aspect[2], aspect[3]);
  if (!webcap.pipeline || !webcap.pipeline.is_rec) {
    // 録画前の場合はバッファの内容をそのまま描画
    webcap.canvas_2d.drawImage(webcap.video, aspect[0], aspect[1], aspect[2], aspect[3]);
    if (!webcap.camera || !webcap.camera.cmd || !webcap.camera.cmd.capture_fps) {
      window.setTimeout(webcap.rec, 1000 / 10);
    } else {
      window.setTimeout(webcap.rec, 1000 / webcap.camera.cmd.capture_fps);
    }
    return;
  }
  // 画像送信
  const capimg = webcap.buffer.toDataURL('image/jpeg');
  const formData = new FormData();
  const blob = new Blob([capimg], {type:"application/octet-stream"});
  formData.append('files', blob);
  fetch(webcap.pipeline.url, {method: "POST", mode:'cors', body: formData}).then((res) => {
    hide_loading();
    if (!res.ok) {
      webcap.message(`Error: ${res.status} ${res.statusText}\nCould not connect to webcap process.`);
      webcap.rec_stop();
    }
  }).catch((e) => {
    webcap.message(`Error: ${e} ${webcap.pipeline.url}`);
    webcap.rec_stop();
  }).finally(() => {
    window.setTimeout(webcap.rec, 1000 / webcap.camera.cmd.capture_fps);
  });
};
/** callbackを表示 */
webcap.callback = () => {
  const protocol = window.location.protocol.endsWith('s:') ? 'wss:' : 'ws:';
  const host = window.location.hostname;
  const port = window.location.port;
  const path = window.location.pathname;
  const ws = new WebSocket(`${protocol}//${host}:${port}${path}/sub_img`);
  const target_elem = $('#out_container');
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const img_url = data['img_url'];
    const img_id = data['img_id'];
    const outputs_key = data['outputs_key'];
    const outputs = data['success'];
    if (img_url) {
      const img = new Image();
      img.onload = () => {
        webcap.canvas_2d.drawImage(img, 0, 0, webcap.canvas.width, webcap.canvas.height);
      }
      img.src = img_url;
    }
    if (outputs) {
      const elem = $("#out_container");
      elem.html('');
      const table = $('<table class="table table-bordered table-hover table-sm"></table>');
      const table_body = $('<tbody></tbody>');
      table.append(table_body);
      elem.append(table);
      const filter_outputs = {},  dst_outputs = {}
      filter_output(outputs, outputs_key, filter_outputs);
      filter_output(filter_outputs, webcap.pipeline.outputs_key_str.split(','), dst_outputs);
      Object.keys(dst_outputs).forEach((key) => {
        const val = dst_outputs[key];
        if (!val) return;
        table_body.append(`<tr class="table_title fs-5" style="overflow-wrap:break-word;word-break:break-all;"><th>${key}</th><td>${val}</td></tr>`);
      });
      table_body.find('tr:first').addClass('fs-1').removeClass('fs-5');
    }
  };
  const filter_output = (src, keys, dst) => {
    for (const key of keys) {
      if (src[key]) {
        dst[key] = src[key];
        continue;
      }
      if (typeof src !== 'object') continue;
      Object.keys(src).forEach((k) => {
        if (typeof src[k] !== 'object') return;
        filter_output(src[k], keys, dst);
      });
    }
  }
}
$(() => {
  show_loading();
  // ダークモード対応
  change_dark_mode(window.matchMedia('(prefers-color-scheme: dark)').matches);
  // copyright情報取得
  const copyright_func = async () => {
    const response = await fetch('copyright');
    const copyright = await response.text();
    $('.copyright').text(copyright);
  };
  copyright_func();
  // webcapモード初期化
  webcap.init();
  // 推論結果受信
  webcap.callback();
});
