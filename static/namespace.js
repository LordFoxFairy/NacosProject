new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],  // 自定义插值语法，避免与 Flask 冲突
    data: {
        namespaces: [],
        namespace: {
            namespaceShowName: '',
            namespaceDesc: ''
        },
        editMode: false,
        isModalActive: false  // 控制模态框的显示
    },
    created() {
        this.fetchNamespaces();
    },
    methods: {
        fetchNamespaces() {
            fetch('api/namespaces')
                .then(response => response.json())
                .then(data => {
                    this.namespaces = data.data;
                });
        },
        navigateToGroups(namespace) {
            window.location.href = `/namespaces/${namespace}/details`;
        },
        openModal() {
            this.isModalActive = true;
            this.resetForm();
        },
        closeModal() {
            this.isModalActive = false;
        },
        editNamespace(ns) {
            this.namespace = { ...ns };
            this.editMode = true;
            this.isModalActive = true;
        },
        saveNamespace() {
            const url = '/api/namespaces';
            const payload = {
                namespace_name: this.namespace.namespaceShowName,
                namespace_desc: this.namespace.namespaceDesc
            };
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                alert(this.editMode ? '命名空间更新成功' : '命名空间添加成功');
                this.fetchNamespaces();
                this.closeModal();
            });
        },
        resetForm() {
            this.namespace = { namespaceShowName: '', namespaceDesc: '' };
            this.editMode = false;
        }
    }
});
