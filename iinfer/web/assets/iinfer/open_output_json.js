// output_jsonファイルを選択して表示する
const open_output_json_func = (target_id) => {
    // ファイル選択後に結果画面を開く
    const view_output_json_func = (current_path) => {
        eel.load_result(current_path)().then((result) => {
            view_result_func(current_path, result);
            hide_loading();
        });
    };
    filer_modal_func(target_id, 'output_json', '', view_output_json_func);
};