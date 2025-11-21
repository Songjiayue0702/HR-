const ADDRESS_DATA = {
    "北京市": {
        "北京市": ["东城区", "西城区", "朝阳区", "海淀区"]
    },
    "上海市": {
        "上海市": ["浦东新区", "徐汇区", "静安区", "闵行区"]
    },
    "广东省": {
        "广州市": ["天河区", "越秀区", "番禺区"],
        "深圳市": ["福田区", "南山区", "罗湖区"]
    },
    "浙江省": {
        "杭州市": ["西湖区", "上城区", "江干区"],
        "宁波市": ["海曙区", "鄞州区"]
    }
};

function populateSelect(selectElement, options, placeholder, selectedValue) {
    if (!selectElement) return;
    selectElement.innerHTML = '';
    const placeholderOption = document.createElement('option');
    placeholderOption.value = '';
    placeholderOption.textContent = placeholder;
    selectElement.appendChild(placeholderOption);
    options.forEach(option => {
        const el = document.createElement('option');
        el.value = option;
        el.textContent = option;
        if (option === selectedValue) {
            el.selected = true;
        }
        selectElement.appendChild(el);
    });
}

function getCities(province) {
    return province && ADDRESS_DATA[province]
        ? Object.keys(ADDRESS_DATA[province])
        : [];
}

function getDistricts(province, city) {
    return province && city && ADDRESS_DATA[province] && ADDRESS_DATA[province][city]
        ? ADDRESS_DATA[province][city]
        : [];
}

function initAddressSelects(prefix, selectedProvince = '', selectedCity = '', selectedDistrict = '') {
    const provinceSelect = document.getElementById(`${prefix}address_province`);
    const citySelect = document.getElementById(`${prefix}address_city`);
    const districtSelect = document.getElementById(`${prefix}address_district`);

    if (!provinceSelect || !citySelect || !districtSelect) return;

    const provinces = Object.keys(ADDRESS_DATA);
    populateSelect(provinceSelect, provinces, '请选择省份', selectedProvince);

    populateSelect(citySelect, getCities(selectedProvince), '请选择城市', selectedCity);
    populateSelect(districtSelect, getDistricts(selectedProvince, selectedCity), '请选择区/县', selectedDistrict);

    provinceSelect.addEventListener('change', function () {
        populateSelect(citySelect, getCities(provinceSelect.value), '请选择城市', '');
        populateSelect(districtSelect, [], '请选择区/县', '');
    });

    citySelect.addEventListener('change', function () {
        populateSelect(districtSelect, getDistricts(provinceSelect.value, citySelect.value), '请选择区/县', '');
    });
}

